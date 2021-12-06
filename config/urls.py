from django.urls import path
from chatbot.views import *
from crolling.views import *

urlpatterns = [
    #### chatbot ####
    path("chatting/", chatWithServer),  # 엔드포인트 : 안드로이드 <-> 백엔드 <-> dialogflow서버
    #### 복지정보 count ####
    path("count-items/", countItems),
    #### 복지 리스트 ####
    path("paged-list/", pagedBokjiroList),  # paging된 복지로 리스트 반환
    path("bokjiro/<str:id>/", bokjoroDetail),  # 복지로 아이템 상세보기
    #### 복지 혜택 ####
    path("benefit/<str:category>/", benefit),  # 복지 혜택 카테고리에 따른 리스트
    path("benefit/detail/<str:id>/", benefitDetail),  # 복지 혜택 디테일
    #### crolling ####
    path("crolling/mohw/all/", crollingAllMohw),  # 보건복지상담센터 FAQ 크롤링 => DB저장
    path("crolling/bokjiro/all/", crollingAllBokjiro),  # 복지로 데이터 크롤링 => DB저장
]
