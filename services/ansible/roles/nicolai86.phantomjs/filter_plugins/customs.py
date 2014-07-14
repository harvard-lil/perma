class FilterModule(object):
  def filters(self):
    return {
      'filename_without_extension': self.filename_without_extension
    }

  def filename_without_extension(self, path, extension):
    return path[:-len(extension)]