# -*- coding:utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 Samsung SDS Co., LTD
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time
import datetime
import uuid
import unittest

from boto.ec2 import regioninfo
from boto.ec2.cloudwatch import CloudWatchConnection
from boto.ec2.cloudwatch.alarm import MetricAlarm
from boto.exception import BotoServerError
import random 
from synaps import exception
from datetime import timedelta

ASYNC_WAIT = 3

class SynapsTestCase(unittest.TestCase):
    def setUp(self):
        access_key = 'changeme'
        secret_key = 'changeme'
        self.synaps = CloudWatchConnection(
            # oss key pair
            aws_access_key_id=access_key, aws_secret_access_key=secret_key,
            is_secure=False, port=8773, path='/monitor',
            region=regioninfo.RegionInfo(None, 'Test Region', 'localhost'),
        )
        
        self.namespace = "SPCS/SYNAPSTEST"
        self.metric_name = "test_metric"
        self.dimensions = {'instance_name':'test instance'}
        
    def tearDown(self):
        pass
        
class ShortCase(SynapsTestCase):
    def test_delete_alarms(self):
        for i in range(10):
            alarm = MetricAlarm(name="TEST_ALARM_%02d" % i,
                metric=self.metric_name, namespace=self.namespace,
                statistic="Average", comparison="<", threshold=2.0 * i,
                period=300, evaluation_periods=2, unit="Percent",
                description=None, dimensions=self.dimensions,
                alarm_actions=None, insufficient_data_actions=None,
                ok_actions=None)
            self.synaps.put_metric_alarm(alarm)

        time.sleep(ASYNC_WAIT)
        
        alarmnames = ["TEST_ALARM_%02d" % i for i in range(10)]
        for alarm in alarmnames:
            self.synaps.delete_alarms(alarms=[alarm])
        
        time.sleep(ASYNC_WAIT)
        
        alarms = self.synaps.describe_alarms()
        for a in alarms:
            self.assertFalse(a.name in alarmnames)

        # should raise 404 exception
        try:
            self.synaps.delete_alarms(alarms=["never_exist_alarmname"])
        except BotoServerError as ex:
            self.assertEqual(ex.error_code, u'404')
        else:
            self.fail("should return 404 error") 
        
    def test_describe_alarm_history(self):
        history_list = self.synaps.describe_alarm_history(
            history_item_type="StateUpdate"
        )
        
        for history in history_list:
            self.assertTrue(history.tem_type, "StateUpdate")
        
    def test_describe_alarms(self):
        for i in range(10):
            alarm = MetricAlarm(name="TEST_ALARM_%02d" % i,
                metric=self.metric_name, namespace=self.namespace,
                statistic="Average", comparison="<", threshold=2.0 * i,
                period=300, evaluation_periods=2, unit="Percent",
                description=None, dimensions=self.dimensions,
                alarm_actions=None, insufficient_data_actions=None,
                ok_actions=None)
            self.synaps.put_metric_alarm(alarm)
                
        alarms = self.synaps.describe_alarms(max_records=3)
        self.assertEqual(len(alarms), 3)

        alarms = self.synaps.describe_alarms(max_records=9,
                                             alarm_name_prefix=u"TEST_")
        self.assertTrue(len(alarms) <= 9)
        for a in alarms:
            self.assertTrue(a.name.startswith("TEST_"))

        alarm_names = ["TEST_ALARM_01", "TEST_ALARM_02"]
        alarms = self.synaps.describe_alarms(max_records=9,
                                             alarm_names=["TEST_ALARM_01"])
        for a in alarms:
            self.assertTrue(a.name in alarm_names)

    
    def test_describe_alarms_for_metric(self):
        for i in range(10):
            alarm = MetricAlarm(name="TEST_ALARM_%02d" % i,
                metric=self.metric_name, namespace=self.namespace,
                statistic="Average", comparison="<", threshold=2.0 * i,
                period=300, evaluation_periods=2, unit="Percent",
                description=None, dimensions=self.dimensions,
                alarm_actions=None, insufficient_data_actions=None,
                ok_actions=None)
            self.synaps.put_metric_alarm(alarm)

        alarms = self.synaps.describe_alarms_for_metric(
            namespace=self.namespace,
            metric_name=self.metric_name,
            dimensions=self.dimensions
        )
    
    def test_get_metric_statistics(self):
        # test_put_metric_data 에서 검증
        pass
     
    def test_list_metrics(self):
        """
        본 테스트 케이스는 list_metrics API를 검증하기 위한 것으로, 메트릭을 
        하나 입력하고, 해당하는 메트릭이 조회되는지 여부를 확인한다.
        """
        # 메트릭 입력        
        ret = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
            value=55.25, unit="Percent", dimensions=self.dimensions,
            timestamp=datetime.datetime.utcnow(),
        )
        self.assertTrue(ret)

        # 메트릭 조회
        ret = self.synaps.list_metrics(
            dimensions=self.dimensions,
            metric_name=self.metric_name,
            namespace=self.namespace
        )
        self.assertTrue(isinstance(ret, list))
    
    def test_list_numeric(self):
        
        try:
            # 메트릭 네임에 숫자가 들어갈 경우 에러가 발생하는지를 검사.
            ret = self.synaps.list_metrics(
                dimensions=None,
                metric_name=None,
                namespace=None
            )
        except BotoServerError:
            self.fail("It should occur an error")
        else:
            self.assertTrue(ret)
            
    
    def test_put_metric_alarm(self):
        alarm_actions = ['+82 1012345678', 'test@email.abc']
        ok_actions = ['+82 1012345678', '+82 1012345678',
                      'tdsadasdest@email.abc']
        insufficient_data_actions = ['+82 1087654322', 'test@email.abc',
                                     'test@email.abc']
        alarm = MetricAlarm(name="CPU_Alarm", metric=self.metric_name,
                            namespace=self.namespace, statistic="Average",
                            comparison=">", threshold=50.0, period=300,
                            evaluation_periods=2, unit="Percent",
                            description=None, dimensions=self.dimensions,
                            alarm_actions=alarm_actions,
                            insufficient_data_actions=insufficient_data_actions,
                            ok_actions=ok_actions)
        self.synaps.put_metric_alarm(alarm)
        
        n = 20
        minute = datetime.timedelta(seconds=60)
        start = datetime.datetime.utcnow() - n * minute 
        for i in range(n):
            ret = self.synaps.put_metric_data(
                namespace=self.namespace, name=self.metric_name,
                value=i * 5.0, unit="Percent", dimensions=self.dimensions,
                timestamp=start + i * minute,
            )
        
        time.sleep(ASYNC_WAIT)
        
        alarms = self.synaps.describe_alarms(alarm_names=['CPU_Alarm'])
        for a in alarms:
            self.assertSetEqual(set(ok_actions), set(a.ok_actions))
            self.assertSetEqual(set(alarm_actions), set(a.alarm_actions))
            self.assertSetEqual(set(insufficient_data_actions),
                                set(a.insufficient_data_actions))

    def test_alarm_actions(self):
        # delete Alarm
        try:
            self.synaps.delete_alarms(alarms=['AlarmActionTest'])
            time.sleep(ASYNC_WAIT)
        except BotoServerError:
            pass
        
        # add Alarm
        alarm_actions = ['+82 1093145616', 'june.yi@samsung.com']
        ok_actions = ['+82 1012345678', '+82 1093145616',
                      'june.yi@samsung.com']
        insufficient_data_actions = ['+82 1093145616', 'june.yi@samsung.com',
                                     'test@email.abc']
        alarm = MetricAlarm(name="AlarmActionTest", metric=self.metric_name,
                            namespace=self.namespace, statistic="Sum",
                            comparison=">", threshold=50.0, period=300,
                            evaluation_periods=2, unit="Percent",
                            description=None, dimensions=self.dimensions,
                            alarm_actions=alarm_actions,
                            insufficient_data_actions=insufficient_data_actions,
                            ok_actions=ok_actions)
        self.synaps.put_metric_alarm(alarm)
        time.sleep(ASYNC_WAIT)
        
        # get MetricStatistics
        n = 10
        minute = datetime.timedelta(seconds=60)
        end_time = datetime.datetime.utcnow()
        start_time = end_time - n * minute
        stats = self.synaps.get_metric_statistics(
            period=60, start_time=start_time, end_time=end_time,
            metric_name=self.metric_name, namespace=self.namespace,
            statistics=["Sum"], dimensions=self.dimensions, unit="Percent"
        )

        for s in stats:
            self.synaps.put_metric_data(
                namespace=self.namespace, name=self.metric_name,
                value= -s["Sum"], timestamp=s['Timestamp'], unit=s["Unit"],
                dimensions=self.dimensions
            )
        
        for i in range(n):
            self.synaps.put_metric_data(
                namespace=self.namespace, name=self.metric_name,
                value=i * 10, unit="Percent", dimensions=self.dimensions,
                timestamp=start_time + i * minute,
            )
        
        time.sleep(ASYNC_WAIT)
        
        # delete alarm        
        self.synaps.delete_alarms(alarms=['AlarmActionTest'])
        time.sleep(ASYNC_WAIT)

        
    def test_put_metric_alarm_check_statistic(self):
        #test check Parameters...
        alarm = MetricAlarm(name="CPU_Alarm", metric=self.metric_name,
                            namespace=self.namespace, 
                            statistic="It will occur an error",
                            comparison=">", threshold=50.0, period=300,
                            evaluation_periods=2, unit="Percent",
                            description=None, dimensions=self.dimensions,
                            alarm_actions=None, insufficient_data_actions=None,
                            ok_actions=None)   
        
        self.assertRaises(BotoServerError, self.synaps.put_metric_alarm, alarm) 
        
    def test_put_metric_alarm_check_unit(self):
        #test check Parameters...        
        alarm = MetricAlarm(name="CPU_Alarm", metric=self.metric_name,
                            namespace=self.namespace, statistic="Average",
                            comparison=">", threshold=50.0, period=300,
                            evaluation_periods=2, 
                            unit="It will occur an error",
                            description=None, dimensions=self.dimensions,
                            alarm_actions=None, insufficient_data_actions=None,
                            ok_actions=None)   
        
        self.assertRaises(BotoServerError, self.synaps.put_metric_alarm, alarm)
    
    def test_samplecount(self):

        now = datetime.datetime.utcnow()
        now_idx = now.replace(second=0, microsecond=0)
        start_time = now - datetime.timedelta(hours=0.1)
        end_time = now

        # Input metric
        ret = self.synaps.put_metric_data(
            namespace=self.namespace, name="SampleCountTest",
            value=1000, unit="Bytes", dimensions=self.dimensions,
            timestamp=now_idx,
        )

        time.sleep(ASYNC_WAIT)
        
        
        # input metric      
        ret = self.synaps.put_metric_data(
            namespace=self.namespace, name="SampleCountTest",
            value=2000, unit="Bytes", dimensions=self.dimensions,
            timestamp=now_idx,
        )

        stata = self.synaps.get_metric_statistics(
            period=300, start_time=start_time, end_time=end_time,
            metric_name="SampleCountTest", namespace=self.namespace,
            statistics=['Sum', 'Average', 'SampleCount'],
            unit="Kilobytes",
            dimensions=self.dimensions,
        )

        statb = self.synaps.get_metric_statistics(
            period=300, start_time=start_time, end_time=end_time,
            metric_name="SampleCountTest", namespace=self.namespace,
            statistics=['Sum', 'Average', 'SampleCount'],
            unit="Bytes",
            dimensions=self.dimensions,
        )

        
        stat1 = filter(lambda x: x.get('Timestamp') == now_idx, stata)[0]
        stat2 = filter(lambda x: x.get('Timestamp') == now_idx, statb)[0]
        
        self.assertAlmostEqual(stat1['SampleCount'], stat2['SampleCount'])
        
        # Ensure zero sample counts are not reported for periods without
        # actual datapoints

        way_before_start = start_time - datetime.timedelta(weeks=20*52) 
        way_before_end = way_before_start + datetime.timedelta(hours=1)

        ancient_stat = self.synaps.get_metric_statistics(
            period=300, start_time=way_before_start, end_time=way_before_end,
            metric_name="SampleCountTest", namespace=self.namespace,
            statistics=['SampleCount'],
            unit="Bytes",
            dimensions=self.dimensions,
        )

        self.assertEqual(len(ancient_stat), 0)

    def test_alarm_period(self):
        
        #알람을 생성, MAX_START_PERIOD 를 6000 으로 증가시키는지 테스트.
        alarm = MetricAlarm(name="Test_Alarm_Period", metric=self.metric_name,
                            namespace=self.namespace, statistic="Average",
                            comparison=">", threshold=50.0, period=6000,
                            evaluation_periods=2, unit="Percent",
                            description=None, dimensions=self.dimensions,
                            alarm_actions=None, insufficient_data_actions=None,
                            ok_actions=None)
        self.synaps.put_metric_alarm(alarm)
        
        # 메트릭의 TimeStamp가 TTL 범위(15일 이내) 를 벗어난 데이터일 경우,
        # DB 에 저장하지 않고 무시하는지 여부를 테스트.
        td = timedelta(days=20, seconds=1) 
        
        ret1 = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
            value=10, unit="Percent", dimensions=self.dimensions,
            timestamp=datetime.datetime.utcnow() - td
        )
        
        # 메트릭의 TimeStamp가 TTL 이내이나 MAX_START_PERIOD 범위 외인 경우,
        # DB에서 해당 time index 를 찾아와 데이터를 입력하는지를 테스트.        
        td2 = timedelta(seconds=7200) 
    
        ret2 = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
            value=20, unit="Percent", dimensions=self.dimensions,
            timestamp=datetime.datetime.utcnow() - td2
        )
        
        self.assertTrue(ret2)
             
        
        # TimeStamp가 현재인 메트릭 입력하여
        # 정상적으로 DB 및 Memory에 입력되는지를 테스트. 
        td3 = timedelta(seconds=5400) 
        
        ret3 = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
        value=30, unit="Percent", dimensions=self.dimensions,
            timestamp=datetime.datetime.utcnow() - td3
        )
       
        self.assertTrue(ret3)
        
        # 위의 알람을 지웠을 경우 MAX_START_PERIOD 가 갱신되는지를 테스트.
        alarmnames = ["Test_Alarm_Period"]
        for alarm in alarmnames:
            self.synaps.delete_alarms(alarms=[alarm])
        
        
        # MAX_START_PERIOD 가 변경된 이후 
        # 메트릭 입력이 정상적으로 진행되는지를 테스트.
        td4 = timedelta(seconds=2000)  
        
        ret4 = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
            value=40, unit="Percent", dimensions=self.dimensions,
            timestamp=datetime.datetime.utcnow() - td4
        )
        
        self.assertTrue(ret4)
        
                
    def test_put_metric_data(self):
        """
        본 테스트 케이스는 put_metric_data API 및 get_metric_statistics API를 
        검증하기 위한 것으로, 메트릭(metric1)을 하나 입력 후, `ASYNC_WAIT` 초 
        sleep 후 통계 데이터(stat1) 요청하고 메트릭(metric2)을 하나 더 입력 후, 
        `ASYNC_WAIT` 초 sleep 후 통계 데이터(stat2)를 다시 요청한다.
        
        stat1과 stat2의 SampleCount 차이는 1이 되어야하며, stat1['Sum']은 
        metric2 value + stat2['Sum']과 같아야한다.
        """
        now = datetime.datetime.utcnow()
        now_idx = now.replace(second=0, microsecond=0)
        start_time = now - datetime.timedelta(hours=0.25)
        end_time = now

        # 메트릭 입력
        ret = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
            value=55.25, unit="Percent", dimensions=self.dimensions,
            timestamp=now_idx,
        )
        self.assertTrue(ret)

        time.sleep(ASYNC_WAIT)
        
        # 메트릭 입력 전 통계자료 조회
        before_stat = self.synaps.get_metric_statistics(
            period=300, start_time=start_time, end_time=end_time,
            metric_name=self.metric_name, namespace=self.namespace,
            statistics=['Sum', 'Average', 'SampleCount'],
            dimensions=self.dimensions,
        )

        test_value = random.random() * 100
        
        
        # 메트릭 입력        
        ret = self.synaps.put_metric_data(
            namespace=self.namespace, name=self.metric_name,
            value=test_value, unit="Percent", dimensions=self.dimensions,
            timestamp=now_idx,
        )
        self.assertTrue(ret)

        # 메트릭 입력 후 통계자료 조회 (비동기 메시지가 처리되는 동안 대기 후)
        time.sleep(ASYNC_WAIT)
        after_stat = self.synaps.get_metric_statistics(
            period=300, start_time=start_time, end_time=end_time,
            metric_name=self.metric_name, namespace=self.namespace,
            statistics=['Sum', 'Average', 'SampleCount'],
            dimensions=self.dimensions,
        )
        
        stat1 = filter(lambda x: x.get('Timestamp') == now_idx, before_stat)[0]
        stat2 = filter(lambda x: x.get('Timestamp') == now_idx, after_stat)[0]
        
        #expected = stat1['Sum'] + test_value
        self.assertAlmostEqual(stat1['Sum'] + test_value, stat2['Sum'])
        
        # expect that the unit matches that specified on the corresponding
        # PutMetricData call, even though we do not explicitly state the
        # in the GetMetricStatistics call
        self.assertEqual(stat2['Unit'], "Percent")

        # check 400 error when period is invalid
        test_period = 50
        try:
            self.synaps.get_metric_statistics(
                period=test_period, start_time=start_time, end_time=end_time,
                metric_name=self.metric_name, namespace=self.namespace,
                statistics=['Sum', 'Average', 'SampleCount'],
                dimensions=self.dimensions,
            )
        except BotoServerError as ex:
            self.assertEqual(ex.error_code, u'400')
        else:
            self.fail("should return 400 error")         

        test_period = 100
        try:
            self.synaps.get_metric_statistics(
                period=test_period, start_time=start_time, end_time=end_time, 
                metric_name=self.metric_name, namespace=self.namespace,
                statistics=['Sum', 'Average', 'SampleCount'],
                dimensions=self.dimensions,
            )
        except BotoServerError as ex:
            self.assertEqual(ex.error_code, u'400')
        else:
            self.fail("should return 400 error")         

    def test_enable_alarm_actions(self):
        for i in range(10):
            alarm = MetricAlarm(name="TEST_ALARM_%02d" % i,
                metric=self.metric_name, namespace=self.namespace,
                statistic="Average", comparison="<", threshold=2.0 * i,
                period=300, evaluation_periods=2, unit="Percent",
                description=None, dimensions=self.dimensions,
                alarm_actions=None, insufficient_data_actions=None,
                ok_actions=None)
            self.synaps.put_metric_alarm(alarm)

        time.sleep(ASYNC_WAIT)

        alarmnames = ["TEST_ALARM_%02d" % i for i in range(10)]
        self.synaps.enable_alarm_actions(alarmnames)
        time.sleep(ASYNC_WAIT)
        alarms = self.synaps.describe_alarms(alarm_names=alarmnames)
        for a in alarms:
            self.assertTrue(a.actions_enabled, 'true')

        self.synaps.disable_alarm_actions(alarmnames)
        time.sleep(ASYNC_WAIT)
        alarms = self.synaps.describe_alarms(alarm_names=alarmnames)
        for a in alarms:
            self.assertEqual(a.actions_enabled, 'false')
        
        for alarm in alarmnames:
            self.synaps.delete_alarms(alarms=[alarm])
        
        time.sleep(ASYNC_WAIT)

        alarms = self.synaps.describe_alarms(alarm_names=alarmnames)
        for a in alarms:
            self.assertFalse(a.name in alarmnames)

    def test_set_alarm_state(self):
        alarmname = "TEST_ALARM_00"
        alarm = MetricAlarm(name=alarmname,
            metric=self.metric_name, namespace=self.namespace,
            statistic="Average", comparison="<", threshold=2.0,
            period=300, evaluation_periods=2, unit="Percent",
            description=None, dimensions=self.dimensions,
            alarm_actions=None, insufficient_data_actions=None,
            ok_actions=None)
        self.synaps.put_metric_alarm(alarm)        

        time.sleep(ASYNC_WAIT)
        
        self.synaps.set_alarm_state(alarmname, state_reason="Manual input",
                                    state_value="ALARM")

        time.sleep(ASYNC_WAIT)
        
        alarms = self.synaps.describe_alarms(alarm_names=[alarmname])
        alarm = alarms[0]
        
        self.assertEqual("ALARM", alarm.state_value)
        self.assertEqual("Manual input", alarm.state_reason)
        
    def test_check_alarm_state(self):
        alarmname = "TEST_ALARM_00"
        alarm = MetricAlarm(name=alarmname,
            metric=self.metric_name, namespace=self.namespace,
            statistic="Average", comparison="<", threshold=2.0,
            period=60, evaluation_periods=1, unit="Percent",
            description=None, dimensions=self.dimensions,
            alarm_actions=None, insufficient_data_actions=None,
            ok_actions=None)
        self.synaps.put_metric_alarm(alarm)        

        time.sleep(ASYNC_WAIT)
        
        self.synaps.set_alarm_state(alarmname, state_reason="Manual input",
                                    state_value="ALARM")

        time.sleep(ASYNC_WAIT)

        for alarm in self.synaps.describe_alarms(alarm_names=[alarmname]):
            self.assertEqual("ALARM", alarm.state_value)
            self.assertEqual("Manual input", alarm.state_reason)

        self.synaps.delete_alarms(alarms=[alarmname])

    def test_utf8_result(self):
        alarm_names = [u"TEST_ALARM_01", u"TEST_알람_02"]
        for alarmname in alarm_names:
            alarm = MetricAlarm(name=alarmname,
                metric=self.metric_name, namespace=self.namespace,
                statistic="Average", comparison="<", threshold=2.0,
                period=300, evaluation_periods=2, unit="Percent",
                description=None, dimensions=self.dimensions,
                alarm_actions=None, insufficient_data_actions=None,
                ok_actions=None)
            self.synaps.put_metric_alarm(alarm)    
        
        alarms = self.synaps.describe_alarms(max_records=9,
                                             alarm_names=["TEST_알람_02"])
        for a in alarms:
            self.assertTrue(a.name in alarm_names)  

    
class LongCase(SynapsTestCase):
    def test_check_alarm_state(self):
        alarmname = "TEST_ALARM_00"
        alarm = MetricAlarm(name=alarmname,
            metric=self.metric_name, namespace=self.namespace,
            statistic="Average", comparison="<", threshold=2.0,
            period=60, evaluation_periods=1, unit="Percent",
            description=None, dimensions=self.dimensions,
            alarm_actions=None, insufficient_data_actions=None,
            ok_actions=None)
        self.synaps.put_metric_alarm(alarm)        

        time.sleep(ASYNC_WAIT)
        
        self.synaps.set_alarm_state(alarmname, state_reason="Manual input",
                                    state_value="ALARM")

        time.sleep(ASYNC_WAIT)

        for alarm in self.synaps.describe_alarms(alarm_names=[alarmname]):
            self.assertEqual("ALARM", alarm.state_value)
            self.assertEqual("Manual input", alarm.state_reason)
        
        time.sleep(90)

        for alarm in self.synaps.describe_alarms(alarm_names=[alarmname]):
            self.assertEqual("INSUFFICIENT_DATA", alarm.state_value)

        self.synaps.delete_alarms(alarms=[alarmname])
        
if __name__ == "__main__":
    unittest.main()
