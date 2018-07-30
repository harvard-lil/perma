import re
import tempfile
from distutils.dir_util import copy_tree
from glob import glob
from shutil import copy

import os
import subprocess
import unittest
from tempdir import TempDir

from django.conf import settings

from perma.tests.utils import failed_test_files_path


class StaticBundlesTestCase(unittest.TestCase):
    def test_static_bundles(self):
        """
            Rebuild static bundles and make sure they match contents of static/bundles/ folder.
        """
        temp_dir = TempDir()
        test_bundle_tracker_file = tempfile.NamedTemporaryFile(dir=settings.PROJECT_ROOT)
        real_bundle_tracker_file = settings.WEBPACK_LOADER['DEFAULT']['STATS_FILE']

        # compile static assets with webpack
        try:
            subprocess.check_output(["./node_modules/.bin/webpack",
                                     "--config", "webpack.config.js",
                                     "--output-path", temp_dir.name],
                                    env=dict(os.environ, BUNDLE_TRACKER_PATH=test_bundle_tracker_file.name[len(settings.PROJECT_ROOT):]))
        except subprocess.CalledProcessError as e:
            self.assertTrue(False, "Error compiling static assets with webpack:\n%s" % e.output)

        # check that compiled assets match
        real_dir = os.path.join(settings.PROJECT_ROOT, 'static/bundles')
        real_files = [i for i in glob(os.path.join(real_dir, "*")) if not i.endswith('.map')]
        test_files = [i for i in glob(os.path.join(temp_dir.name, "*")) if not i.endswith('.map')]
        errors = []
        for test_file in test_files:
            real_file = os.path.join(real_dir, os.path.basename(test_file))

            # check for missing files
            if real_file not in real_files:
                errors.append("Missing file: %s" % real_file)
                continue

            # check for non-matching files
            if open(test_file, 'rb').read() != open(real_file, 'rb').read():
                errors.append("File needs to be regenerated: %s" % real_file)

        # check for extra files
        for extra_file in set(os.path.basename(i) for i in real_files) - set(os.path.basename(i) for i in test_files):
            errors.append("Unexpected file in static/bundles: %s" % extra_file)

        # check webpack-stats.json
        if not os.path.exists(real_bundle_tracker_file):
            errors.append("File missing: %s" % real_bundle_tracker_file)
        else:
            # Use a regex to remove substrings like "path":"somestuff",
            # so we can compare webpack stats files generated on different systems.
            # This is fine since "path" isn't used on production.
            remove_path_re = re.compile(r'"path":"[^"]*?"')
            test_tracker_contents = remove_path_re.sub('', open(test_bundle_tracker_file.name).read())
            real_tracker_contents = remove_path_re.sub('', open(real_bundle_tracker_file).read())
            if test_tracker_contents != real_tracker_contents:
                errors.append("File needs to be regenerated: %s" % real_bundle_tracker_file)

        # report errors
        if errors:
            # write generated files to failed_test_files_path
            copy_tree(temp_dir.name, os.path.join(failed_test_files_path, 'bundles'))
            copy(test_bundle_tracker_file.name, os.path.join(failed_test_files_path, os.path.basename(real_bundle_tracker_file)))

            message = """
Errors checking webpack output:\n- %s
Try running `npm run build` to update the static/bundles/ folder.
See failed_test_files folder for generated files.
""" % "\n- ".join(errors)
            self.assertTrue(False, message)


