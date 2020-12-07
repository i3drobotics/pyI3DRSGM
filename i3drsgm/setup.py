"""Setup module to build i3drsgm module"""
from os.path import abspath, dirname, join, normpath, relpath
from shutil import rmtree
import glob
import sys
import argparse
from setuptools import Command, setup, find_packages
from i3drsgm import I3DRSGMAppAPI


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './i3drsgm/i3drsgm_app ./i3drsgm/tmp ./i3drsgm-* '
    CLEAN_FILES += './build ./dist ./*.pyc ./*.tgz ./*.egg-info ./__pycache__'
    CLEAN_FILES = CLEAN_FILES.split(' ')
    # Support the "all" option. Setuptools expects it in some situations.
    user_options = [
        ('all', 'a',
         "provided for compatibility, has no extra functionality")
    ]

    boolean_options = ['all']

    def __init__(self, dist):
        self.all = None
        super().__init__(dist)

    def initialize_options(self):
        """Inital options for clean command"""
        self.all = None

    def finalize_options(self):
        """Finalise options for clean command"""

    def run(self):
        """Run clean command"""
        script_path = normpath(abspath(dirname(__file__)))
        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(normpath(join(script_path, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(script_path):
                    # Die if path in CLEAN_FILES
                    # is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (
                        path, script_path))
                print('removing %s' % relpath(path))
                rmtree(path)


with open("../README.md", "r") as fh:
    long_description = fh.read()


with open("../version.txt", "r") as fh:
    version = fh.read()


def str2bool(bool_str):
    """Convert string with boolean value to bool type"""
    if isinstance(bool_str, bool):
        return bool_str
    if bool_str.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif bool_str.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


# Get custom command line options
# TODO: replace this with setuptools cmdclass
# (can't work out how to change setuptools.setup arguments from a cmdclass)
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('--offline-installer', type=str2bool, default=False,
                       help='required foo argument', required=False)
args, unknown = argparser.parse_known_args()
sys.argv = [sys.argv[0]] + unknown

# Define custom options
OFFLINE_INSTALLER = args.offline_installer

if OFFLINE_INSTALLER:
    INCLUDE_PACKAGE_DATA = True
    I3DRSGMAppAPI.download_app()
else:
    INCLUDE_PACKAGE_DATA = False

setup(
    name="i3drsgm",
    version=version,
    author="Ben Knight",
    author_email="bknight@i3drobotics.com",
    description="Python wrapper for I3DR Semi-Global Matcher",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/i3drobotics/pyi3drsgm",
    packages=find_packages(),
    package_dir={'i3drsgm': 'i3drsgm'},
    include_package_data=INCLUDE_PACKAGE_DATA,
    install_requires=[
        'numpy; python_version == "3.5"',
        'numpy==1.19.3; python_version > "3.5"',
        'opencv-python', 'stereo3d >= 0.0.3', "wget"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.6',
    cmdclass={'clean': CleanCommand}
)
