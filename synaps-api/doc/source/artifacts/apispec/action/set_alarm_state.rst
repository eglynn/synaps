.. _set_alarm_state:

SetAlarmState
=============

설명
----
임시로 알람의 상태를 정한다. 상태는 지속되지 않고 다음 알람 체크 시 실제 상태로
변경된다.

요청 매개변수
-------------
공통으로 요구되는 매개변수는 :ref:`common_query_parameters` 를 참고한다.

.. list-table:: 
   :widths: 20 50 10
   :header-rows: 1

   * - 이름
     - 설명
     - 필수 여부
   * - AlarmName
     - 알람 이름. SPCS 사용자의 알람 내에서 유일한 이름을 가져야 함. 

       자료 형: String

       길이 제한: 최소 1자 ~ 최대 255자
              
       형식 제한: 숫자로만 이루어진 값 사용 불가
     - Yes
   * - StateReason
     - 사람이 읽기 좋은 텍스트 형식으로 알람의 상태가 변경된 이유를 기술함 

       자료 형: String

       길이 제한: 최소 1자 ~ 최대 1203자
              
       형식 제한: 숫자로만 이루어진 값 사용 불가
     - Yes
   * - StateReasonData
     - JSON 형식으로 알람의 상태가 변경된 이유를 기술함

       자료 형: String

       길이 제한: 최소 0자 ~ 최대 4000자
              
       형식 제한: 숫자로만 이루어진 값 사용 불가
     - No
   * - StateValue
     - 상태 값

       자료 형: String

       유효 값: OK | ALARM | INSUFFICIENT_DATA
     - Yes       
     
에러
----
공통으로 발생하는 에러는 :ref:`common_errors` 를 참고한다.

.. list-table:: 
   :widths: 20 50 10
   :header-rows: 1
   
   * - 에러
     - 설명
     - HTTP Status Code
   * - InvalidFormat
     - 데이터가 유효한 JSON 형식이 아님
     - 400  
   * - ResourceNotFound
     - 해당하는 이름의 알람이 없음
     - 404