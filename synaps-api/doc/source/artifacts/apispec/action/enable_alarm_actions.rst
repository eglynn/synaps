.. _enable_alarm_actions:

EnableAlarmActions
==================

설명
----
특정 알람의 액션을 활성화 함.

요청 매개변수
-------------
공통으로 요구되는 매개변수는 :ref:`common_query_parameters` 를 참고한다.

.. list-table:: 
   :widths: 20 50 10
   :header-rows: 1

   * - 이름
     - 설명
     - 필수 여부
   * - AlarmNames.member.N
     - 액션을 활성화 할 알람 이름의 리스트

       자료 형: String 리스트

       길이 제한: 최소 0개부터 최대 100개의 아이템
     - Yes

에러
----
공통으로 발생하는 에러는 :ref:`common_errors` 를 참고한다.
