#!/usr/bin/env python3
"""Run the installed STM32CubeMX on an IOC and optionally build its CMake project."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def quoted(path):
    value = str(path)
    if any(char in value for char in ('"', '\r', '\n')):
        raise ValueError('CubeMX paths cannot contain quotes or line breaks')
    return '"' + value + '"'


def launcher(path, java):
    if path.is_dir() and path.suffix == '.app':
        path = path / 'Contents' / 'MacOS' / 'STM32CubeMX'
    if not path.is_file():
        raise ValueError('CubeMX executable was not found')
    if path.suffix.lower() in ('.exe', '.jar'):
        java_path = java or str(path.parent / 'jre' / 'bin' / 'java.exe')
        if path.suffix.lower() == '.jar' and not java:
            java_path = shutil.which('java') or java_path
        if not Path(java_path).is_file():
            raise ValueError('Java was not found. Supply --java or CUBEMX_JAVA')
        return [str(java_path), '-jar', str(path)]
    return [str(path)]


def run(args):
    ioc = args.ioc.resolve(strict=True)
    if ioc.suffix.lower() != '.ioc':
        raise ValueError('--ioc must point to an IOC file')
    if args.timeout <= 0:
        raise ValueError('--timeout must be positive')
    properties = {}
    for line in ioc.read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            properties[key] = value
    project_name = properties.get('ProjectManager.ProjectName') or ioc.stem
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', project_name):
        raise ValueError('Use an ASCII project name containing letters, digits and underscores')
    prefix = launcher(args.cubemx.resolve(), args.java)
    project = ioc.parent
    state = project / '.cubemx-local'
    state.mkdir(exist_ok=True)
    script = state / 'generate.txt'
    log = state / 'generation.log'
    commands = [
        'config load ' + quoted(ioc),
        'project name ' + project_name,
        'project toolchain CMake',
        'config save ' + quoted(ioc),
        'project generate',
        'exit',
    ]
    script.write_text('\n'.join(commands) + '\n', encoding='utf-8')
    try:
        with log.open('wb') as output:
            result = subprocess.run(
                prefix + ['-q', str(script)], cwd=project,
                stdout=output, stderr=subprocess.STDOUT, timeout=args.timeout,
            )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('CubeMX timed out. Inspect .cubemx-local/generation.log') from error
    output = log.read_text(encoding='utf-8', errors='replace')
    generation = output.rsplit('project generate', 1)
    if result.returncode or len(generation) != 2 or re.search(r'^KO\b', output, re.MULTILINE):
        raise RuntimeError('CubeMX failed. Inspect .cubemx-local/generation.log')
    if not re.search(r'^OK\s*$', generation[1], re.MULTILINE):
        raise RuntimeError('CubeMX did not confirm generation. Inspect the local log')
    required = ['CMakeLists.txt', 'CMakePresets.json', 'cmake/gcc-arm-none-eabi.cmake']
    missing = [name for name in required if not (project / name).is_file()]
    if missing:
        raise RuntimeError('Missing generated files: ' + ', '.join(missing))
    if 'OptionalMessage_ERROR' in output:
        print('CubeMX emitted import diagnostics. Review the local log and generated configuration.')
    print('CubeMX generated the CMake project.')
    if args.build:
        subprocess.run(['cmake', '--preset', args.preset], cwd=project, check=True)
        subprocess.run(['cmake', '--build', '--preset', args.preset], cwd=project, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ioc', type=Path, required=True)
    parser.add_argument('--cubemx', type=Path, default=os.environ.get('CUBEMX_PATH'))
    parser.add_argument('--java', default=os.environ.get('CUBEMX_JAVA'))
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--preset', default='Debug')
    args = parser.parse_args()
    if args.cubemx is None:
        parser.error('Supply --cubemx or set CUBEMX_PATH')
    try:
        run(args)
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
