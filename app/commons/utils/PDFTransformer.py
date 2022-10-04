import pdfkit, unicodedata, re


class PDFTransformer:

    def __init__(self, app):
        self.logger = app.logger

    def convert_file(self, file, output=None):
        self.logger.info("creating PDF from {file}".format(file=file))
        output = output if output else "%s.pdf" % file.split(".")[0]
        pdfkit.from_file(file,output)
        return output

    def dump_url(self, url, output=None):
        self.logger.info("creating PDF from {url}".format(url=url))
        output = output if output else "%s.pdf" % self.slugify(url)
        pdfkit.from_url(url, output)
        return output

    def from_string(self, string, output=None):
        name = string[:10] if len(string) > 10 else string
        self.logger.info("creating PDF from string: '{string}'".format(string=name))
        output = output if output else "%s.pdf" % self.slugify(name)
        pdfkit.from_string(string, output)
        return output

    @staticmethod
    def slugify(value):
        """
        Converts to lowercase, removes non-word characters (alphanumerics and
        underscores) and converts spaces to hyphens. Also strips leading and
        trailing whitespace.
        """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub('[^\w\s-]', '', value).strip().lower()
        return "-".join(re.sub('[-\s]+', '-', value))
