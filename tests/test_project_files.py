"""Regression checks for portable documentation and file discovery."""
import unittest

from tools.check_project_files import destination, markdown_links, verify


class ProjectFilesTests(unittest.TestCase):
    def test_live_repository_contract(self):
        self.assertEqual(verify()['unresolved_current_links'], 0)

    def test_missing_and_case_mismatch_fail_even_on_windows(self):
        files = {'docs/Guide.md'}
        self.assertEqual(destination('README.md', 'docs/guide.md', files)[0], 'MISSING_OR_CASE_MISMATCH')
        self.assertEqual(destination('README.md', 'docs/Guide.md', files)[0], 'TRACKED')

    def test_relative_paths_images_spaces_and_external_files(self):
        files = {'README.md', 'docs/A B.md', 'docs/image.png'}
        self.assertEqual(destination('docs/A B.md', '../README.md#start', files)[0], 'TRACKED')
        self.assertEqual(destination('README.md', 'docs/A%20B.md', files)[0], 'TRACKED')
        self.assertEqual(destination('README.md', '../outside.md', files)[0], 'OUTSIDE_REPOSITORY')
        self.assertEqual(destination('README.md', 'https://example.invalid/test', files)[0], 'EXTERNAL')
        self.assertEqual(list(markdown_links('![image](docs/image.png)')), [(1, 'docs/image.png')])

    def test_fenced_examples_and_inline_code_are_not_links(self):
        source = '```md\n[missing](missing.md)\n```\n`[also](missing.md)`\n[valid](README.md)'
        self.assertEqual(list(markdown_links(source)), [(5, 'README.md')])

    def test_reference_definitions_and_missing_references(self):
        self.assertEqual(list(markdown_links('[guide][ID]\n\n[id]: <docs/A B.md>')), [(1, 'docs/A B.md')])
        with self.assertRaisesRegex(ValueError, 'undefined Markdown reference'):
            list(markdown_links('[guide][missing]'))

    def test_directories_must_have_tracked_children(self):
        self.assertEqual(destination('README.md', 'reports/', {'reports/example.md'})[0], 'TRACKED')
        self.assertEqual(destination('README.md', 'reports/', {'README.md'})[0], 'MISSING_OR_CASE_MISMATCH')
