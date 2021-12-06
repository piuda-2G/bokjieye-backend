from datetime import time
import json, os, requests, xmltodict
from config.settings import BASE_DIR, API_KEY
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.cloud import dialogflow
from proto import Message
from chatbot.elasticSearchService import *
from .models import *

# dialogFlow서버에서 결과 받아오기
# return : 리턴된 응답 메시지, 응답한 인텐트 이름, 입력된 파라미터들 Object
def getDialogflowResult(project_id, location_id, session_id, text, language_code):
    # 동일한 세션ID로 통신을 하면 지속적인 대화가 가능 (약 20분 유지)
    session_client = dialogflow.SessionsClient(
        client_options={"api_endpoint": f"{location_id}-dialogflow.googleapis.com"}
    )
    session = f"projects/{project_id}/locations/{location_id}/agent/sessions/{session_id}"

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    # dialogflow의 결과를 dict로 변환
    dict_response = Message.to_dict(response)
    fulfillment_text = dict_response.get("query_result").get("fulfillment_text")
    recent_intent = dict_response.get("query_result").get("intent").get("display_name")
    params = dict_response.get("query_result").get("parameters")

    return fulfillment_text, recent_intent, params


# Client(안드로이드)의 dialogFlow 통신용 엔드 포인트
# input : {"texts":"내용", "sessionId":"세션ID"}
# output : {"input texts":"입력내용", "result texts":"결과내용", "sessionId":"세션ID", "resultData":{최종결과오브젝트})
@csrf_exempt
def chatWithServer(request):

    SESSION_ID = json.loads(request.body)["sessionId"]
    inputText = json.loads(request.body)["texts"]

    # 환경변수 GOOGLE_APPLICATION_CREDENTIALS 등록하면 Google Cloud SDK가 알아서 사용자 계정으로 인증처리
    credentials = os.path.join(BASE_DIR, "credentials.json")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials

    PROJECT_ID = "welfare-chat-gm9e"
    LANGUAGE_CODE = "ko"
    LOCATION_ID = "asia-northeast1"
    # dialogflow에서 문장 받아오기 : (응답텍스트, 응답한 인텐트이름, 파라미터객체)
    result_texts, intent_name, params = getDialogflowResult(
        PROJECT_ID, LOCATION_ID, SESSION_ID, inputText, LANGUAGE_CODE
    )
    # 클라이언트에 응답할 데이터
    response = {"input texts": inputText, "result texts": result_texts, "sessionId": SESSION_ID}

    # From 추천 : 최종결과 리턴 트리거 => 인텐트 이름 : "Recommend_F - custom - custom - yes"
    resultData = None
    searchFlag = False
    if intent_name == "Recommend_F - custom2 - custom - yes":
        resultData = searchBokjiroByParams(params["age"], params["area"], params["interest"])
        if len(resultData):
            resultData = resultData[0]["_source"]
            response.update({"fromBokjiro": True})
        else:
            response["result texts"] = "일치하는 복지 결과가 없습니다. 보건복지 상담센터로 연결하시겠습니까?"
            response.update({"noResults": True})
            resultData = None
        response.update({"fromRecommend": True})
    # From 검색 : 최종결과 리턴 트리거 => 인텐트 이름 : "Search - custom"
    if intent_name == "Search - custom":
        if len(params["any"]):
            keyword = " ".join(params["any"])
        if len(params["Others"]):
            keyword = " ".join(params["Others"])
        resultData, source = searchBykeyword(keyword)
        if source == "bokjiro":
            response.update({"fromBokjiro": True})
        response.update({"sessionInit": True})
        searchFlag = True
    # 최종적으로 반환되는 결과 오브젝트가 존재하면 추가해서 반환
    if resultData:
        response.update({"resultData": resultData})

    # 전화연결 yes or no
    if not searchFlag:
        if intent_name == "Recommend_F - custom2 - custom - yes - yes":
            itemId = json.loads(request.body).get("request_id") or None
            if itemId is not None:
                phone = GetBokjoroPhone(itemId)
            else:
                phone = "129"
            response.update({"call": True, "number": phone})
            if phone == "129":
                response["result texts"] = ""
                response.update({"exist": False})
            else:
                response["result texts"] = ""
                response.update({"exist": Truex})
        if intent_name == "Recommend_F - custom2 - custom - yes - no":
            response[
                "result texts"
            ] = "전화를 연결을 하지 않겠습니다. 다시 복지정보 추천을 원하실 경우 추천, 검색을 원하실 경우 검색이라 말해주세요."
            response.update({"call": False})
    return JsonResponse(response, safe=False)


# 인자로 page, central, local, keyword를 받아서 elasticsearch에서 페이지네이션 된 data 반환
@csrf_exempt
def pagedBokjiroList(request):
    page = int(request.GET.get("page", 1))
    central = request.GET.get("central", None)
    local = request.GET.get("local", None)
    keyword = request.GET.get("keyword", None)
    results = getPagedList(page, central, local, keyword)
    for item in results:
        if not item["_source"]["contents"]:
            item["_source"]["contents"] = "자세한 내용을 원하시면 클릭해주세요."
    return JsonResponse(results, safe=False)


@csrf_exempt
# 전체 복지정보, 신규 복지정보 counter
def countItems(request):
    context = countDocuments()
    return JsonResponse(context, safe=False)


@csrf_exempt
# 복지정보 detail 정보 return
def bokjoroDetail(request, id):
    # 복지로 자료 ID
    DOMAIN = "http://apis.data.go.kr/B554287/NationalWelfareInformations/NationalWelfaredetailed"

    params = f"?serviceKey={API_KEY}&callTp=D&servId={id}"
    response = requests.get(DOMAIN + params).content.decode("utf-8")
    parsedDict = xmltodict.parse(response).get("wantedDtl", {})
    rawPhones = parsedDict.get("inqplCtadrList", {})
    processedPhones = []
    if isinstance(rawPhones, list):
        for item in rawPhones:
            if item.get("servSeDetailLink", None) and item.get("servSeDetailNm", None):
                processedPhones.append(
                    {"number": item["servSeDetailLink"], "name": item["servSeDetailNm"]}
                )
    else:
        if rawPhones.get("servSeDetailLink", None) and rawPhones.get("servSeDetailNm", None):
            processedPhones.append(
                {"number": rawPhones["servSeDetailLink"], "name": rawPhones["servSeDetailNm"]}
            )

    item_id = parsedDict.get("servId") or ""
    title = parsedDict.get("servNm") or ""
    contents = parsedDict.get("alwServCn") or ""
    target = parsedDict.get("tgtrDtlCn") or ""
    department = parsedDict.get("jurMnofNm") or ""
    if not department:
        department = Bokjiro.objects.get(id=item_id).address + " 주관"
    result = {
        "id": item_id,  # id
        "title": title,  # 서비스이름
        "contents": contents,  # 서비스내용
        "target": target,  # 지원대상
        "department": department,  # 소관부처명
        "phones": processedPhones,  # 연락가능번호 List
    }
    return JsonResponse(result, safe=False)


def benefit(request, category):
    items = Benefit.objects.filter(field=category)
    listItems = list(items.values())

    return JsonResponse(listItems, safe=False)


def benefitDetail(request, id):
    id = int(id)
    item = Benefit.objects.get(id=id)
    result = {
        "title": item.title,
        "contents": item.contents,
        "who": item.who,
        "howTo": item.howTo,
        "field": item.field,
    }

    return JsonResponse(result, safe=False)


# 복지정보 detail 정보 return
def GetBokjoroPhone(id):
    # 복지로 자료 ID
    DOMAIN = "http://apis.data.go.kr/B554287/NationalWelfareInformations/NationalWelfaredetailed"

    params = f"?serviceKey={API_KEY}&callTp=D&servId={id}"
    response = requests.get(DOMAIN + params).content.decode("utf-8")
    parsedDict = xmltodict.parse(response).get("wantedDtl", {})
    print(parsedDict)
    rawPhones = parsedDict.get("inqplCtadrList", {})
    processedPhones = []
    if isinstance(rawPhones, list):
        for item in rawPhones:
            if item.get("servSeDetailLink", None) and item.get("servSeDetailNm", None):
                processedPhones.append(
                    {"number": item["servSeDetailLink"], "name": item["servSeDetailNm"]}
                )
    else:
        if rawPhones.get("servSeDetailLink", None) and rawPhones.get("servSeDetailNm", None):
            processedPhones.append(
                {"number": rawPhones["servSeDetailLink"], "name": rawPhones["servSeDetailNm"]}
            )

    if len(processedPhones):
        return processedPhones[0]["number"].replace("-", "")
    else:
        return "129"
