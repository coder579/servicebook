import os
import re
import json
import yaml

import requests_mock
from servicebook.tests.support import BaseTest


class ApiTest(BaseTest):

    def test_browsing_project(self):
        projects = self.app.get('/api/project').json['data']
        absearch_id = projects[0]['id']

        bz_matcher = re.compile('.*bugzilla.*')
        bz_resp = {'bugs': []}
        sw_matcher = re.compile('search.stage.mozaws.net.*')
        yamlf = os.path.join(os.path.dirname(__file__), '__api__.yaml')

        with open(yamlf) as f:
            sw_resp = yaml.load(f.read())

        with requests_mock.Mocker() as m:
            m.get(bz_matcher, text=json.dumps(bz_resp))
            m.get(sw_matcher, text=json.dumps(sw_resp))
            absearch = self.app.get('/api/project/%d' % absearch_id)
            self.assertEqual(absearch.json['data']['qa_primary_id'], 3)

    def test_browsing_user(self):
        karl_json = self.app.get('/api/user/3').json['data']
        self.assertEqual(karl_json['firstname'], 'Karl')

    def test_browsing_group(self):
        group = self.app.get('/api/group/Customization').json['data']
        self.assertEqual(group['name'], 'Customization')

    def test_changing_user(self):
        resp = self.app.get('/api/user/3')
        etag = resp.etag
        karl_json = resp.json['data']
        self.assertEqual(karl_json['firstname'], 'Karl')
        karl_json['firstname'] = 'K.'
        req_data = {'data': {'type': 'user', 'attributes': karl_json,
                    'id': '3'}}

        headers = {'If-Match': etag,
                   'Content-Type': 'application/vnd.api+json'}

        self.app.patch_json('/api/user/3', params=req_data,
                            headers=headers)
        resp = self.app.get('/api/user/3')
        karl_json = resp.json['data']
        etag = resp.etag
        self.assertEqual(karl_json['firstname'], 'K.')

        # now test the etag value
        resp = self.app.get('/api/user/3',
                            headers={'If-None-Match': str(etag)})
        self.assertEqual(resp.status_int, 304)
        self.app.get('/api/user/3', headers={'If-None-Match': "MEH"})
