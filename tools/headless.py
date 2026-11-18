#!/usr/bin/env python3
"""Small libretro frontend for testing the real ROM without a desktop window.

The emulator executes the 68000, VDP and PSG. This frontend supplies controller
buttons, reads the ROM's public debug state, and optionally saves video/audio.
It does not implement the game or its algorithms.
"""
from __future__ import annotations

import argparse
import ctypes as C
import json
from pathlib import Path
import struct
import sys
import tempfile

DEFAULT_CORE = Path.home() / ".config/retroarch/cores/genesis_plus_gx_libretro.so"


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.c_void_p), ("size", C.c_size_t), ("meta", C.c_char_p)]


class SystemInfo(C.Structure):
    _fields_ = [("library_name", C.c_char_p), ("library_version", C.c_char_p),
                ("valid_extensions", C.c_char_p), ("need_fullpath", C.c_bool), ("block_extract", C.c_bool)]


class Variable(C.Structure):
    _fields_ = [("key", C.c_char_p), ("value", C.c_char_p)]


ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDIO_BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

# Standard Genesis Plus GX libretro layout: A=Y, B=B, C=A.
BUTTONS = {"A": 1, "B": 0, "C": 8, "START": 3, "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7}


class Emulator:
    def __init__(self, rom, core=DEFAULT_CORE):
        self.rom = Path(rom).resolve()
        self.core_path = Path(core).resolve()
        self.pixel_format = 0
        self.buttons = set()
        self.options = {}
        self.option_overrides = {
            b"genesis_plus_gx_region_detect": b"ntsc-u",
            b"genesis_plus_gx_bios": b"disabled",
        }
        self.environment_calls = set()
        self.callback_errors = []
        self.capture_video = True
        self.capture_audio = False
        self.video = None
        self.audio = bytearray()
        self.frames = 0
        self.word_swap = None
        self.loaded = False
        self.temp = tempfile.TemporaryDirectory(prefix="sonic-algorithm-lab-")
        self.directory = self.temp.name.encode()
        self.core = C.CDLL(str(self.core_path))
        callbacks = [("environment", ENV, self._environment), ("video_refresh", VIDEO, self._video),
                     ("audio_sample", AUDIO, self._audio), ("audio_sample_batch", AUDIO_BATCH, self._audio_batch),
                     ("input_poll", POLL, lambda: None), ("input_state", INPUT, self._input)]
        self.callbacks = []
        for name, signature, function in callbacks:
            callback = signature(function)
            self.callbacks.append(callback)
            setter = getattr(self.core, "retro_set_" + name)
            setter.argtypes = [signature]
            setter.restype = None
            setter(callback)
        for name in ("retro_init", "retro_deinit", "retro_run", "retro_reset", "retro_unload_game"):
            getattr(self.core, name).argtypes = []
            getattr(self.core, name).restype = None
        self.core.retro_get_system_info.argtypes = [C.POINTER(SystemInfo)]
        self.core.retro_get_system_info.restype = None
        self.core.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        self.core.retro_load_game.restype = C.c_bool
        self.core.retro_get_memory_data.argtypes = [C.c_uint]
        self.core.retro_get_memory_data.restype = C.c_void_p
        self.core.retro_get_memory_size.argtypes = [C.c_uint]
        self.core.retro_get_memory_size.restype = C.c_size_t
        self.core.retro_set_controller_port_device.argtypes = [C.c_uint, C.c_uint]
        self.core.retro_set_controller_port_device.restype = None
        self.info = SystemInfo()
        self.core.retro_get_system_info(C.byref(self.info))
        self.core.retro_init()
        self.rom_bytes = C.create_string_buffer(self.rom.read_bytes())
        self.game = GameInfo(str(self.rom).encode(), C.cast(self.rom_bytes, C.c_void_p),
                             len(self.rom_bytes) - 1, None)
        if not self.core.retro_load_game(C.byref(self.game)):
            raise RuntimeError("Emulator rejected ROM")
        self.loaded = True
        self.core.retro_set_controller_port_device(0, 1)
        self.core.retro_set_controller_port_device(1, 0)
        self.ram_pointer = self.core.retro_get_memory_data(2)
        self.ram_size = self.core.retro_get_memory_size(2)
        if not self.ram_pointer or self.ram_size < 65536:
            raise RuntimeError(f"Core did not expose Genesis work RAM: {self.ram_size}")
        self.ram_array = (C.c_ubyte * self.ram_size).from_address(self.ram_pointer)

    def _environment(self, cmd, data):
        self.environment_calls.add(cmd)
        try:
            base = cmd & 0xFFFF
            if base in (9, 30, 31):  # system, content, save directories
                C.cast(data, C.POINTER(C.c_char_p))[0] = self.directory
                return True
            if base == 3:  # GET_CAN_DUPE
                C.cast(data, C.POINTER(C.c_bool))[0] = True
                return True
            if base == 10:  # SET_PIXEL_FORMAT
                self.pixel_format = C.cast(data, C.POINTER(C.c_int))[0]
                return self.pixel_format in (0, 1, 2)
            if base == 16:  # SET_VARIABLES (legacy options)
                variables = C.cast(data, C.POINTER(Variable))
                for i in range(1024):
                    if not variables[i].key:
                        break
                    choices = variables[i].value.split(b";", 1)[-1].strip().split(b"|")
                    self.options[variables[i].key] = choices[0]
                return True
            if base == 15:  # GET_VARIABLE
                variable = C.cast(data, C.POINTER(Variable)).contents
                value = self.option_overrides.get(variable.key, self.options.get(variable.key))
                variable.value = value
                return value is not None
            if base == 17:  # GET_VARIABLE_UPDATE
                C.cast(data, C.POINTER(C.c_bool))[0] = False
                return True
            if base == 52:  # GET_CORE_OPTIONS_VERSION: use legacy options
                C.cast(data, C.POINTER(C.c_uint))[0] = 0
                return True
            if base in (39, 57):  # English; legacy disk control interface
                C.cast(data, C.POINTER(C.c_uint))[0] = 0
                return True
            if base == 47:  # GET_AUDIO_VIDEO_ENABLE
                C.cast(data, C.POINTER(C.c_int))[0] = 3
                return True
            if base in (1, 6, 11, 18, 32, 35, 36, 37):
                return True
            return False
        except Exception as exc:
            self.callback_errors.append(f"environment {cmd}: {exc}")
            return False

    def _video(self, data, width, height, pitch):
        if self.capture_video and data and data != C.c_void_p(-1).value:
            self.video = (C.string_at(data, height * pitch), width, height, pitch, self.pixel_format)

    def _audio(self, left, right):
        if self.capture_audio:
            self.audio.extend(struct.pack("<hh", left, right))

    def _audio_batch(self, data, frames):
        if self.capture_audio:
            self.audio.extend(C.string_at(data, frames * 4))
        return frames

    def _input(self, port, device, index, button):
        if port != 0 or (device & 255) != 1:
            return 0
        if button == 256:
            return sum(1 << b for b in self.buttons)
        return int(button in self.buttons)

    def run(self, frames=1, buttons=()):
        self.buttons = {BUTTONS[b.upper()] if isinstance(b, str) else b for b in buttons}
        for _ in range(frames):
            self.core.retro_run()
        self.frames += frames
        if self.callback_errors:
            raise RuntimeError(self.callback_errors)

    def press(self, button, frames=2):
        self.run(frames, [button])
        self.run(2)

    def ram(self, start=0, count=0x58):
        raw = bytes(self.ram_array[start:start + count])
        if self.word_swap is None:
            magic = bytes(self.ram_array[:4])
            if magic == b"SAL1":
                self.word_swap = False
            elif magic == b"AS1L":
                self.word_swap = True
            else:
                raise RuntimeError(f"ROM has not initialized (RAM magic {magic!r})")
        if self.word_swap:
            return bytes(self.ram_array[(start + i) ^ 1] for i in range(count))
        return raw

    def poke(self, offset, data):
        self.ram()  # detect byte order
        for i, value in enumerate(data):
            self.ram_array[(offset + i) ^ int(self.word_swap)] = value

    def state(self):
        b = self.ram()
        words = {"algorithm": 0x08, "dataset": 0x0A, "running": 0x0C, "done": 0x0E,
                 "phase": 0x10, "timer": 0x12, "comparisons": 0x14, "swaps": 0x16,
                 "outer": 0x18, "index": 0x1A, "pass": 0x1C, "pass_swapped": 0x1E,
                 "pair_left": 0x20, "pair_right": 0x22, "want_swap": 0x24, "message": 0x26,
                 "last_left": 0x28, "last_right": 0x2A, "sonic_x": 0x30,
                 "jump_y": 0x32, "jump_velocity": 0x34, "facing": 0x36,
                 "moving": 0x38, "sonic_frame": 0x3A, "auto_delay": 0x3C, "fault": 0x50}
        state = {key: struct.unpack_from(">H", b, offset)[0] for key, offset in words.items()}
        for key in ("pair_left", "pair_right", "jump_y", "jump_velocity"):
            if state[key] >= 32768:
                state[key] -= 65536
        state.update(frame=int.from_bytes(b[4:8], "big"), values=list(b[0x40:0x48]),
                     ids=list(b[0x48:0x50]), joy=b[0x2C], pressed=b[0x2D],
                     fault_pc=int.from_bytes(b[0x54:0x58], "big"))
        return state

    def image(self):
        from PIL import Image
        if self.video is None:
            raise RuntimeError("No video frame captured")
        raw, width, height, pitch, fmt = self.video
        if fmt == 1:
            return Image.frombytes("RGB", (width, height), raw, "raw", "BGRX", pitch)
        rgb = bytearray(width * height * 3)
        for y in range(height):
            row = struct.unpack_from("<" + str(width) + "H", raw, y * pitch)
            for x, pixel in enumerate(row):
                if fmt == 2:
                    r, g, b = (pixel >> 11) & 31, (pixel >> 5) & 63, pixel & 31
                    color = (r * 255 // 31, g * 255 // 63, b * 255 // 31)
                else:
                    r, g, b = (pixel >> 10) & 31, (pixel >> 5) & 31, pixel & 31
                    color = (r * 255 // 31, g * 255 // 31, b * 255 // 31)
                pos = (y * width + x) * 3
                rgb[pos:pos + 3] = bytes(color)
        return Image.frombytes("RGB", (width, height), bytes(rgb))

    def screenshot(self, path, scale=3):
        from PIL import Image
        self.capture_video = True
        self.run(2)
        im = self.image()
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
        im.save(path)
        return path

    def close(self):
        if self.loaded:
            self.core.retro_unload_game()
            self.loaded = False
        self.core.retro_deinit()
        self.temp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--core", type=Path, default=DEFAULT_CORE)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--press", action="append", default=[])
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    with Emulator(args.rom, args.core) as emulator:
        emulator.run(120)
        for button in args.press:
            emulator.press(button)
        emulator.run(args.frames)
        if args.screenshot:
            emulator.screenshot(args.screenshot)
        print(json.dumps({"core": emulator.info.library_name.decode(),
                          "version": emulator.info.library_version.decode(),
                          "state": emulator.state(), "pixel_format": emulator.pixel_format,
                          "video": list(emulator.video[1:4]) if emulator.video else None}, indent=2))


if __name__ == "__main__":
    main()
