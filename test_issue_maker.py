import unittest
import re
from flask import Flask, request
from werkzeug import ImmutableMultiDict
from swaglyrics import __version__
from issue_maker import update, genius_stripper, check_song, add_stripper
from issue_maker import passwd
from issue_maker import del_line
from unittest.mock import patch
from app import app


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.song = '거품 안 넘치게 따라줘 [Life Is Good] (feat. Crush, Dj Friz)'
        self.artist = 'Dynamic Duo'
        self.correct_title = f'{self.song} by {self.artist}'
        self.path = 'I don\'t know'

    def tearDown(self):
        pass

    def test_update(self):
        app = Flask(__name__)
        with app.test_request_context('/'):
            """Test for correct return if version != request.form['version']"""
            request.form = ImmutableMultiDict([('version', str(__version__) + 'bla')])  # faulty version
            request.form = ImmutableMultiDict([('song', 'Sweeter Without You')])  # song in unsupported.txt
            request.form = ImmutableMultiDict([('artist', 'Borgeous')])  # artist in unsupported.txt
            self.assertEqual(update(), 'Please update SwagLyrics to the latest version to get better support :)')

            """Test if right return if version below 1.0.0"""
            request.form = ImmutableMultiDict([('version', '0.0.9')])  # version below 1.0.0
            self.assertEqual(update(), 'Please update SwagLyrics to the latest version to get better support :)')

            """Test correct output given song and artist that exist in unsupported.txt"""
            request.form = ImmutableMultiDict([('version', str(__version__))])  # correct version
            self.assertEqual(update(), 'Issue already exists on the GitHub repo. \n')

    def test_genius_stripper(self):
        """ Mock perfect input & request.get(), check for intended return """
        # M_(song, artist) must be proved already valid!
        with patch('request.get') as mocked_get:
            mocked_get.json()['meta']['status'] = 200
            mocked_get.json()['response']['hits']['result']['full_title'] = self.correct_title
            mocked_get.json()['response']['hits']['result']['path'] = self.path

            gstr = re.compile(r'(?<=/)[-a-zA-Z0-9]+(?=-lyrics$)')
            path = gstr.search(mocked_get.json()['response']['hits']['result']['path'])
            test_stripper = path.group()

            Stripper = genius_stripper(self.song, self.artist)
            mocked_get.assert_called_with('https://api.genius.com/search')  # If doesn't work due to lack of token, del.

            '''Test for correct stripper '''
            self.assertEqual(Stripper('River (feat. Ed Sheeran)', 'Eminem'), 'Eminem-River')
            self.assertEqual(Stripper("Ain't My Fault - R3hab Remix", 'Zara Larsson'), 'Zara-Larsson-Aint-My-Fault')
            self.assertEqual(Stripper('1800-273-8255', 'Logic'), 'Logic-1800-273-8255')
            self.assertEqual(Stripper('Garota', 'Erlend Øye'), 'Erlend-ye-Garota')
            self.assertEqual(Stripper('Scream & Shout', 'will.i.am'), 'william-Scream-and-Shout')
            self.assertEqual(Stripper('Heebiejeebies - Bonus', 'Aminé'), 'Amine-Heebiejeebies')
            self.assertEqual(Stripper('FRÜHLING IN PARIS', 'Rammstein'), 'Rammstein-FRUHLING-IN-PARIS')
            self.assertEqual(Stripper(
                'Chanel (Go Get It) [feat. Gunna & Lil Baby]', 'Young Thug'), 'Young-Thug-Chanel-Go-Get-It')
            self.assertEqual(Stripper(
                'MONOPOLY (with Victoria Monét)', 'Ariana Grande'), 'Ariana-Grande-and-Victoria-Monet-MONOPOLY')
            self.assertEqual(Stripper('Seasons (with Sjava & Reason)', 'Mozzy'), 'Mozzy-Sjava-and-Reason-Seasons')
            self.assertEqual(Stripper(
                '거품 안 넘치게 따라줘 [Life Is Good] (feat. Crush, Dj Friz)', 'Dynamic Duo'), 'Dynamic-Duo-Life-Is-Good')
            self.assertEqual(Stripper('Ice Hotel (ft. SZA)', 'XXXTENTACION'), 'XXXTENTACION-Ice-Hotel')

            # Test if returns None with invalid inputs
            Faulty_Condition = genius_stripper('Invalid', 'Invalid')
            self.assertEqual(Faulty_Condition, None)

    def test_check_song(self):
        with patch('request.get') as mocked_get:
            # test for if True return if data is fully legit
            mocked_get.json()['tracks']['items'][0]['name'] = self.song
            mocked_get.json()['tracks']['items'][0]['artists'][0]['name'] = self.artist
            self.assertEqual(check_song(self.song, self.artist), True)

            # test for if False return if data is empty
            mocked_get.json()['tracks']['items'] = ''
            self.assertEqual(check_song(self.song, self.artist), False)

    def test_master_unsupported(self):
        with open('unsupported.txt', 'r') as f:
            test_data = f.read()
            tester = app.test_client(self)
            response = tester.get('/master_unsupported')
            self.assertIn(response.data, test_data)

    def test_add_stripper(self):
        app = Flask(__name__)
        with app.test_request_context('/'):
            request.form = ImmutableMultiDict([('auth', passwd)])
            cnt = del_line(self.song, self.artist)
            self.assertEqual(add_stripper, f"Added stripper for {self.song} by {self.artist} to server database "
                                           f"successfully, deleted {cnt} instances from unsupported.txt")


if __name__ == '__main__':
    unittest.main()
