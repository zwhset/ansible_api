# -*- coding: utf-8 -*-

"""
    package.module
    ~~~~~~~~~~~~~~

    Star cloud -> Jenkins -> dsl

    :copyright: (c) YEAR by zwhset.
    :license: GOMEOPS, see LICENSE_FILE for more details.
"""

import jenkins
import requests
import json
import sys

class UpdateDsl(object):

    def __init__(self, job_name, war_name,
                 jenkins_url='http://jenkins.cloud.com',
                 jenkins_user='',
                 jenkines_pass='',
                 dsl_token=''):
        self.job_name = job_name
        self.war_name = '/data/file/jenkins_home/workspace/%s/target/%s' % (job_name,war_name)
        self.jenkins_url = jenkins_url
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkines_pass
        self.dsl_token = dsl_token

    def init_jenkins(self, url, username, password):
        server = jenkins.Jenkins(url, username, password)
        # 判断项目是否存在
        if not server.job_exists(self.job_name):
            raise ValueError, 'job_name: %s not fund. ' % self.job_name
        job_info = server.get_job_info(self.job_name)

        # 判断项目是否编译
        if not job_info.get('lastBuild', {}).get('number', None):
            raise ValueError, 'job_name: %s not build ' % self.job_name

        build_num = job_info['lastBuild']['number']

        job_build_info = server.get_build_info(self.job_name, build_num)
        # 判断是否编译成功
        if job_build_info['result'].lower()  != 'success':
            raise ValueError, 'job_name:%s build Fail' % self.job_name

        changes = server.get_build_info(self.job_name, build_num).get('changeSet', {})
        build_num_url = 'http://jenkis.cloud.com/job/%s/%s/console' % (self.job_name, build_num)

        result = {
            'build_number' : build_num,
            'changes' : changes,
            'build_num_url' : build_num_url
        }
        return result

    def run(self):
        '''发送包数据以及元数据到DSL'''

        # 从星云检索公司-业务-项目
        if '_' in self.job_name:
            job_name = self.job_name.split('_')[-1]
        else:
            job_name = ''.join(self.job_name.split('-')[2:])

        url = 'http://ops.cloud.com:9527/api/dsl/get_application_info/%s' % job_name

        r = requests.get(url)
        result = r.json()

        if result.get('code', 1) != 0:
            raise ValueError, 'get api not fund job_name, error_info: %s' % data.get('message', '')

        data = result['data']
        if len(data) != 1: # 检查是否有多个重名的项目
            raise ValueError, '有多个重名的job_name，系统无法确定选用哪个'

        # 触发传包工作
        info = data[0]
        to_url = 'http://ops.cloud.com:9527/api/dsl/%s/%s/%s/%s' % (info['company_en_name'],
                                                                       info['business_en_name'],
                                                                       info['project_en_name'],
                                                                       info['application_en_name'])

        files = {
            "file": (self.war_name, open(self.war_name, "rb"))
        }

        data = self.init_jenkins(self.jenkins_url, self.jenkins_user, self.jenkins_pass)
        data['token'] = self.dsl_token
        data = {'data':json.dumps(data)} # 接口就这样给的

        r = requests.post(to_url, data=data, files=files)
        data = r.json()
        if data.get('code', 1) != 0:
            raise ValueError, data.get('message', '')
        print '传包成功', data.get('message','')

if __name__ == '__main__':
    jbn = sys.argv[1]
    wrn = sys.argv[2]
    u = UpdateDsl(jbn, wrn)
    u.run()

