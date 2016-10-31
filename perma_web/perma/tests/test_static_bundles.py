import tempfile
from glob import glob
import os
import subprocess
import unittest
from tempdir import TempDir

from django.conf import settings


class StaticBundlesTestCase(unittest.TestCase):
    def test_static_bundles(self):
        """
            Rebuild static bundles and make sure they match contents of static/bundles/ folder.
        """
        temp_dir = TempDir()
        test_bundle_tracker_file = tempfile.NamedTemporaryFile(dir=settings.PROJECT_ROOT)

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
            if open(test_file).read() != open(real_file).read():
                errors.append("File needs to be regenerated: %s" % real_file)

        # check for extra files
        for extra_file in set(os.path.basename(i) for i in real_files) - set(os.path.basename(i) for i in test_files):
            errors.append("Unexpected file in static/bundles: %s" % extra_file)

        # check webpack-stats.json
        real_bundle_tracker_file = os.path.join(settings.PROJECT_ROOT, 'webpack-stats.json')
        if not os.path.exists(real_bundle_tracker_file):
            errors.append("File missing: %s" % real_bundle_tracker_file)
        else:
            test_tracker_contents = open(test_bundle_tracker_file.name).read().replace(temp_dir.name,'')
            real_tracker_contents = open(real_bundle_tracker_file).read().replace(real_dir,'')
            if test_tracker_contents != real_tracker_contents:
                errors.append("File needs to be regenerated: %s" % real_bundle_tracker_file)

        # report errors
        if errors:
            print "Errors checking webpack output:\n- %s\nTry running `npm run build` to fix." % "\n- ".join(errors)
            self.assertTrue(False, "Errors in compiled webpack output -- check log for details.")
