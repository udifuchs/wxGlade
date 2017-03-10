"""
@copyright: 2012-2017 Carsten Grohmann

@license: MIT (see LICENSE.txt) - THIS PROGRAM COMES WITH NO WARRANTY
"""

# import general python modules
import difflib
import errno
import fnmatch
import glob
import os.path
import re
import sys
import types
import unittest

# import project modules
import codegen, common, config, compat, log
from xml_parse import CodeWriter


class WXGladeBaseTest(unittest.TestCase):
    """\
    Provide basic functions for all tests

    All test cases uses an own implementation to L{common.save_file()} to
    catch the results. This behaviour is limited to single file creation.
    """

    _encodings = {}
    """\
    Cached file encodings from L{_get_encoding()} to accelerate the lookup.

    @type: dict[str, str]
    @see: L{_get_encoding()}
    """

    _encoding_content = []
    """\
    Cache content of the encoding file 'file_encodings.txt'

    @type: list[str]
    """

    curr_dir = '.%s' % os.path.sep
    """\
    Platform specific version of "./"

    @type: str
    @see: L{_with_curr_dir()}
    """

    vFiles = {}
    """\
    Dictionary to store the content of the files generated by the code
    generators.

    The filename is the key and the content is a StringIO instance.
    """

    orig_app_encoding = {}
    """\
    Original values for code generator app_encoding instance variable.

    @see: L{codegen.BaseLangCodeWriter.app_encoding}
    """

    orig_file_exists = None
    """\
    Reference to the original L{codegen.BaseLangCodeWriter._file_exists()}
    implementation
    """

    orig_for_version = {}
    """\
    Original values for code generator for_version instance variable.

    @see: L{codegen.BaseLangCodeWriter.for_version}
    """

    orig_load_file = None
    """\
    Reference to the original L{codegen.BaseSourceFileContent._load_file()}
    implementation
    """

    orig_os_access = None
    """\
    Reference to original C{os.access()} implementation
    
    @see: L{_os_access()}
    @see: L{non_accessible_directories}
    """

    orig_os_makedirs = None
    """\
    Reference to original C{os.makedirs()} implementation
    
    @see: L{_os_makedirs()}
    """

    orig_os_path_isdir = None
    """\
    Reference to original C{os.path.isdir()} implementation
    
    @see: L{_os_path_isdir()}
    @see. L{existing_directories}
    """

    orig_save_file = None
    """\
    Reference to the original L{common.save_file()} implementation
    """

    caseDirectory = 'casefiles'
    """\
    Directory with input files and result files
    """

    language_constants = [
        ('python', 'Python', '.py'),
        ('perl', 'Perl', '.pl'),
        ('lisp', 'Lisp', '.lisp'),
        ('XRC', 'XRC', '.xrc'),
        ('C++', 'CPP', '.cpp'),
    ]
    """\
    Language specific constants for file names.

    Each tuple contains three elements:
     - Language
     - File prefix
     - File extension

    @type: list[(str, str, str)]
    """

    existing_directories = []
    """\
    List of writable directories

    @type: list[str]
    @see: L{_os_path_isdir()}
    """

    non_accessible_directories = []
    """\
    List of non-accessible directories

    @type: list[str]
    @see: L{_os_access()}
    """

    non_accessible_files = ''
    """\
    Prefix of non-writable files in writable directories

    @type: str
    @see: L{_save_file()}
    """

    @classmethod
    def setUpClass(cls):
        "Initialise parts of wxGlade before individual tests starts"
        # set icon path back to the default default
        config.icons_path = 'icons'

        # initialise wxGlade preferences and set some useful values
        common.init_preferences()
        config.preferences.autosave = False
        config.preferences.write_timestamp = False
        config.preferences.show_progress = False

        # Determinate case directory
        cls.caseDirectory = os.path.join(
            os.path.dirname(__file__),
            cls.caseDirectory,
            )

        # disable bug dialogs
        sys._called_from_test = True

        # cache content to reduce IO
        fe = open(os.path.join(cls.caseDirectory, 'file_encodings.txt'))
        for line in fe.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            cls._encoding_content.append(line)

        # platform specific list of existing / non-accessible directories
        cls.existing_directories = [
            ".",
            '.%s' % os.path.sep,
            os.path.normpath('/tmp'),
            os.path.normpath('/'),
            os.path.normpath('/non-writable'),
        ]
        cls.non_accessible_directories = [
            os.path.normpath('/non-writable')
        ]
        cls.non_accessible_files = \
            os.path.normpath('/tmp/existing_but_no_access')

    @classmethod
    def tearDownClass(cls):
        "Cleanup after all individual tests are done"
        # de-register own logging
        log.deinit()

    def setUp(self):
        "Initialise"
        # initiate empty structure to store files and there content
        self.vFiles = {}

        # replace some original implementations by test specific implementation
        self.orig_save_file = common.save_file
        common.save_file = self._save_file
        self.orig_load_file = codegen.BaseSourceFileContent._load_file
        codegen.BaseSourceFileContent._load_file = self._fixture_filename(
            codegen.BaseSourceFileContent._load_file)
        self.orig_file_exists = codegen.BaseLangCodeWriter._file_exists
        self.orig_os_access = os.access
        os.access = self._os_access
        self.orig_os_makedirs = os.makedirs
        os.makedirs = self._os_makedirs
        self.orig_os_path_isdir = os.path.isdir
        os.path.isdir = self._os_path_isdir
        codegen.BaseLangCodeWriter._file_exists = self._file_exists
        codegen.BaseLangCodeWriter._show_warnings = False

        # save code generator settings
        for lang in common.code_writers:
            self.orig_for_version[lang] = \
                common.code_writers[lang].for_version
            self.orig_app_encoding[lang] = \
                common.code_writers[lang].app_encoding

    def tearDown(self):
        "Cleanup"
        # cleanup virtual files
        for filename in self.vFiles:
            self.vFiles[filename].close()
        self.vFiles = {}

        # restore original implementations
        common.save_file = self.orig_save_file
        codegen.BaseSourceFileContent._load_file = self.orig_load_file
        codegen.BaseLangCodeWriter._file_exists = self.orig_file_exists
        os.access = self.orig_os_access
        os.makedirs = self.orig_os_makedirs
        os.path.isdir = self._os_path_isdir

        # restore code generator settings
        for lang in common.code_writers:
            common.code_writers[lang].for_version = \
                self.orig_for_version[lang]
            common.code_writers[lang].app_encoding = \
                self.orig_app_encoding[lang]

    def _get_encoding(self, filename):
        """\
        Return file encoding based on pattern in "file_encodings.txt"

        @rtype: str | None
        @see: L{self._encodings}
        """
        if filename in self._encodings:
            return self._encodings[filename]

        for line in self._encoding_content:
            pattern, encoding = line.split(' ', 1)
            if fnmatch.fnmatch(filename, pattern):
                if encoding.upper() == 'NONE':
                    encoding = None
                self._encodings[filename] = encoding
                return encoding

        return None

    def _generate_code(self, language, document, filename):
        """\
        Generate code for the given language.

        @param language: Language to generate code for
        @type language:  str
        @param document: XML document to generate code for
        @type document:  str
        @param filename: Name of the virtual output file
        @type filename:  str
        """
        self.failUnless( language in common.code_writers, "No codewriter loaded for %s" % language )
        self.failUnless(isinstance(document, compat.unicode), 'Expected unicode document, got "%s"'%type(document))

        document = self._prepare_wxg(language, document)

        # CodeWrite need UTF-8 like all XML parsers
        document = document.encode('UTF-8')

        # generate code
        CodeWriter( writer=common.code_writers[language], input=document, from_string=True, out_path=filename )

        return

    def _file_exists(self, filename):
        "Check if the file is a test case file"
        fullpath = os.path.join(self.caseDirectory, filename)
        exists = os.path.isfile(fullpath)
        self.failIf( not exists, 'Case file %s does not exist' % filename )
        return exists

    def _load_file(self, filename):
        """\
        Load a file need by a test case.

        @note: wxg files will be converted to unicode.

        @param filename:  Name of the file to load
        @type filename:   str
        @return:          File content
        @rtype:           str | unicode
        """
        abs_filename = self._get_abs_filename(filename)

        fh = open(abs_filename)
        content = fh.read()
        fh.close()

        # convert encoding back to unicode
        encoding = self._get_encoding(filename)
        if encoding:
            content = content.decode(encoding)

        # replacing path entries
        content = content % {
            'wxglade_path':   config.wxglade_path,
            'docs_path':      config.docs_path,
            'icons_path':     config.icons_path,
            'manual_file':    config.manual_file,
            'widgets_path':   config.widgets_path,
            'templates_path': config.templates_path,
            'tutorial_file':  config.tutorial_file,
            }

        return content

    def _get_abs_filename(self, filename):
        """\
        Return the absolute filename of a file from a test case

        @param filename:  Name of the file to load
        @type filename:   str

        @rtype: str
        """
        casename, extension = os.path.splitext(filename)
        if extension == '.wxg':
            filetype = 'input'
        else:
            filetype = 'result'

        casename_pattern = ['%s%s']
        if extension == '.py':
            casename_pattern.insert(0, '%s_Classic%s' if compat.IS_CLASSIC else '%s_Phoenix%s')

        for pattern in casename_pattern:
            abs_name = os.path.join(self.caseDirectory, pattern % (casename, extension))
            if os.path.isfile(abs_name):
                return abs_name

        self.fail('No %s file "%s" for case "%s" found! Currently generated files: %s' %
                  (filetype, filename, casename, ', '.join(self.vFiles)))

    def get_content(self, filename):
        """Return the content of the specified file or raise an test failure"""
        if filename not in self.vFiles:
            self.fail('File "%s" not found. Currently generated files: %s' % (filename, ', '.join(self.vFiles)))
        return self.vFiles[filename].getvalue()

    def _fixture_filename(self, func):
        """\
        Decorator for adapting filenames to load files from test case
        directory.

        @see: L{codegen.BaseSourceFileContent._load_file()}
        """
        def inner(klass, filename):
            casename, extension = os.path.splitext(filename)

            file_list = glob.glob( os.path.join(self.caseDirectory, "%s%s" % (casename, extension)) )
            self.failIf( len(file_list) == 0, 'No result file for case "%s" found!' % casename)
            self.failIf( len(file_list) > 1,  'More than one result file for case "%s" found!' % casename)

            filename = file_list[0]
            return func(klass, filename)

        return inner

    def _modify_attrs(self, content, **kwargs):
        "Modify general options inside a wxg (XML) file"
        modified = content
        for option in kwargs:
            # create regexp first
            pattern = r'%s=".*?"' % option
            modified = re.sub( pattern, '%s="%s"' % (option, kwargs[option]), modified, 1 )

        return modified

    def _os_access(self, path, mode):
        """\
        Fake implementation for C{os.access()}

        @see: L{non_accessible_directories}
        """
        if path in self.non_accessible_directories:
            return False
        return True

    def _os_makedirs(self, path, mode):
        "Fake implementation for C{os.makedirs()} - do nothing"
        pass

    def _os_path_isdir(self, s):
        "Fake implementation for C{os.path.isdir()}  @see: L{existing_directories}"
        if s in self.existing_directories:
            return True
        return False

    def _prepare_wxg(self, language, document):
        """\
        Set test specific options inside a wxg (XML) file

        @param language: Language to generate code for
        @type language:  str
        @param document: XML document to generate code for
        @type document:  str

        @return: Modified XML document
        @rtype:  str
        """
        _document = self._modify_attrs(
            document,
            language=language,
            indent_amount='4',
            indent_symbol='space',
        )
        return _document

    def _save_file(self, filename, content, which='wxg'):
        """\
        Test specific implementation of L{common.save_file()} to get the
        result of the code generation without file creation.

        The file content is stored in a StringIO instance. It's
        accessible at L{self.vFiles} using the filename as key.

        @note: The signature is as same as L{wxglade.common.save_file()} but
               the functionality differs.

        @param filename: Name of the file to create
        @param content:  String to store into 'filename'
        @param which:    Kind of backup: 'wxg' or 'codegen'
        """
        self.failIf( filename in self.vFiles, "Virtual file %s already exists" % filename )
        self.failUnless( filename, "No filename given" )
        if self.non_accessible_files and \
           filename.startswith(self.non_accessible_files):
            raise IOError(errno.EACCES, os.strerror(errno.EACCES), filename)
        else:
            outfile = compat.StringIO()
            outfile.write(content)
            self.vFiles[filename] = outfile

    def _test_all(self, base, excluded=None):
        """\
        Generate code for all languages based on the base file name
        
        @param base: Base name of the test files
        @type base: str
        @param excluded: Languages to exclude from test
        @type excluded:  list[str]
        """
        for lang, dummy, ext in self.language_constants:
            if excluded and lang in excluded:
                continue
            name_wxg = '%s.wxg' % base
            name_lang = '%s%s' % (base, ext)

            if lang == 'C++':
                self._generate_and_compare_cpp(name_wxg, name_lang)
            else:
                self._generate_and_compare(lang, name_wxg, name_lang)

    def _diff(self, text1, text2):
        """\
        Compare two lists, tailing spaces will be removed

        @param text1: Expected text
        @type text1:  str
        @param text2: Generated text
        @type text2:  str

        @return: Changes formatted as unified diff
        @rtype:  str
        """
        self.assertTrue(isinstance(text1, types.StringTypes))
        self.assertTrue(isinstance(text2, types.StringTypes))

        # split into lists, because difflib needs lists and remove
        # tailing spaces
        list1 = [x.rstrip() for x in text1.splitlines()]
        list2 = [x.rstrip() for x in text2.splitlines()]

        # remove version line "generated by wxGlade"
        for line in list1[:10]:
            if 'generated by wxGlade' in line:
                list1.remove(line)
                break

        for line in list2[:10]:
            if 'generated by wxGlade' in line:
                list2.remove(line)

        # compare source files
        diff_gen = difflib.unified_diff(list1, list2, fromfile='expected source', tofile='created source', lineterm='')
        return '\n'.join(diff_gen)

    def _generate_and_compare(self, lang, inname, outname):
        """\
        Generate code and compare generated and expected code

        @param lang:    Language to generate code for
        @type lang:     str
        @param inname:  Name of the XML input file
        @type inname:   str
        @param outname: Name of the output file
        @type outname:  str
        """
        source = self._load_file(inname)
        expected = self._load_file(outname)

        self._generate_code(lang, source, outname)

        # convert from file encoding back to unicode
        generated = self.get_content(outname)
        encoding = self._get_encoding(outname)
        if encoding:
            generated = generated.decode(encoding)

        self._compare(expected, generated)

    def _generate_and_compare_cpp(self, inname, outname):
        """\
        Generate C++ code and compare generated and expected code

        @param inname:  Name of the XML input file
        @type inname:   str
        @param outname: Name of the output file
        @type outname:  str
        """
        # strip cpp file extension
        base, ext = os.path.splitext(outname)
        if ext:
            outname = base

        name_h = '%s.h' % outname
        name_cpp = '%s.cpp' % outname

        source = self._load_file(inname)
        result_cpp = self._load_file(name_cpp)
        result_h = self._load_file(name_h)

        self._generate_code('C++', source, outname)

        # convert from file encoding back to unicode
        generated_cpp = self.get_content(name_cpp)
        encoding_cpp = self._get_encoding(name_cpp)
        if encoding_cpp:
            generated_cpp = generated_cpp.decode(encoding_cpp)

        generated_h = self.get_content(name_h)
        encoding_h = self._get_encoding(name_h)
        if encoding_h:
            generated_h = generated_h.decode(encoding_h)

        self._compare(result_cpp, generated_cpp, 'C++ source')
        self._compare(result_h, generated_h, 'C++ header')

    def _compare(self, expected, generated, filetype=None):
        """\
        Compare two text documents using a diff algorithm

        @param expected:  Expected content
        @type expected:   str
        @param generated: Generated content
        @type generated:  str
        @param filetype:  Short description of the content
        @type filetype:   str
        """
        # compare files
        delta = self._diff(expected, generated)

        if filetype:
            self.failIf( delta, "Generated %s file and expected result differs:\n%s" % (filetype, delta) )
        else:
            self.failIf( delta, "Generated file and expected result differs:\n%s" % delta )

    def _with_curr_dir(self, filename):
        'Return the filename with prepended platform specific version of "./"   @see: L{curr_dir}'
        return '%s%s' % (self.curr_dir, filename)
