"""Regression tests for CubeMX command failures and incomplete generated output."""

import importlib.util
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'cubemx_generate.py'
SPEC = importlib.util.spec_from_file_location('cubemx_generate', SCRIPT)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class GenerationResults(unittest.TestCase):
    def exercise(self, output, existing_files):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            ioc = project / 'Board.ioc'
            ioc.write_text('ProjectManager.ProjectName=Board\n', encoding='ascii')
            for name in existing_files:
                path = project / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('', encoding='ascii')
            args = SimpleNamespace(
                ioc=ioc, cubemx=project / 'CubeMX', java=None,
                timeout=10, build=False, preset='Debug',
            )

            def fake_process(command, **kwargs):
                kwargs['stdout'].write(output.encode('ascii'))
                return subprocess.CompletedProcess(command, 0)

            with patch.object(GENERATOR, 'launcher', return_value=['CubeMX']):
                with patch.object(GENERATOR.subprocess, 'run', side_effect=fake_process):
                    GENERATOR.run(args)

    def test_failed_command_is_rejected_despite_later_ok_and_existing_files(self):
        output = 'project path invalid\nKO\nproject generate\nOK\nexit\nBye bye\n'
        existing = ['CMakeLists.txt', 'CMakePresets.json', 'cmake/gcc-arm-none-eabi.cmake']
        with self.assertRaisesRegex(RuntimeError, 'CubeMX failed'):
            self.exercise(output, existing)

    def test_incomplete_cmake_output_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Missing generated files'):
            self.exercise('project generate\nOK\nexit\nBye bye\n', ['CMakeLists.txt'])

    def test_success_requires_confirmation_and_expected_files(self):
        files = ['CMakeLists.txt', 'CMakePresets.json', 'cmake/gcc-arm-none-eabi.cmake']
        self.exercise('project generate\nOK\nexit\nBye bye\n', files)


if __name__ == '__main__':
    unittest.main()
