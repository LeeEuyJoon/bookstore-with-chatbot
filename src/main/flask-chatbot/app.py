import tiktoken
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
from database import get_product, get_cart, get_FAQ, get_notice, get_QNA,get_order, add_to_cart
from api_specifi import get_api_routes
from review_sentiment import eval_sentiment
from review_sentiment import review_update
import re
import requests


load_dotenv()

app = Flask(__name__)
# CORS 설정
CORS(app)


api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

messages = []

# 전역 변수 선언
cust_id = ""
prod_id = ""
cust_id_tmp = ""

# tiktoken을 이용해 토큰 수를 계산하는 함수
def calculate_token_usage(conversation, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = sum([len(encoding.encode(message['content'])) for message in conversation])
    return tokens

@app.route('/')
def home():
    return "Hello, Flask!"

def make_prompt(conversation):
    # OpenAI API를 사용해 AI 답변 생성
    res = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=conversation
    )
    return res.choices[0].message.content

def determine_db_query(system_conversation):
    res_db_decision_maker = make_prompt(system_conversation)
    return res_db_decision_maker

@app.route('/chatbot', methods=["GET", "POST"])
def chatbot():
    global cust_id, prod_id, cust_id_tmp  # 함수 내에서 global 변수 선언

    if request.method == "POST":
        # 현재 cust_id와 이전 cust_id를 비교하여 다를 경우 대화 초기화
        if cust_id_tmp != cust_id:
            cust_id_tmp = cust_id  # 새로운 cust_id로 업데이트
            global messages
            messages = [msg for msg in messages if msg['role'] not in ['user', 'assistant']]

        # POST 요청으로 받은 사용자 입력 처리
        user_input = request.json.get("message")

        # 사용자 입력을 바탕으로 어떤 테이블을 조회할 지 결정
        conversation_to_db_decision_maker = [{"role": "system", "content": few_shot_db_decision_maker()}]
        conversation_to_db_decision_maker.append({"role": "user", "content": user_input})
        db_to_query = determine_db_query(conversation_to_db_decision_maker)  # product, cart, api_specifi, no 중 하나 반환

        # 공통 시스템 프롬프트 생성
        conversation = [{"role": "system", "content": few_shot_common()}]

        # 필요한 DB 조회 수행
        if db_to_query == "cart":
            print("<< 챗봇이 장바구니 테이블을 조회합니다. >>")
            data = get_cart(cust_id)
            conversation.append(
                {"role": "system", "content": f"이건 사용자의 장바구니 데이터야: {data}"}
            )
        elif db_to_query == "product":
            print("<< 챗봇이 상품 테이블을 조회합니다. >>")
            data = get_product()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 상품 데이터야: {data}"}
            )
        elif db_to_query == "api_specifi":
            print("<< 챗봇이 api 명세를 조회합니다. >>")
            data = get_api_routes()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 api 명세야: {data}"}
            )
        elif db_to_query == "faq":
            print("<< 챗봇이 faq 테이블을 조회합니다. >>")
            data = get_FAQ()
            api = get_api_routes()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 faq 데이터야: {data}"}
            )
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 api 명세야 : {api}"}
            )
        elif db_to_query == "notice":
            print("<< 챗봇이 notice 테이블을 조회합니다. >>")
            data = get_notice()
            api = get_api_routes()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 notice 데이터야: {data}"}
            )
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 api 명세야 : {api}"}
            )
        elif db_to_query == "order":
            print("<< 챗봇이 order 테이블을 조회합니다. >>")
            data = get_order(cust_id)
            api = get_api_routes()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 order 데이터야: {data}"}
            )
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 api 명세야 : {api}"}
            )
        else:
            print("<< 챗봇이 어떤 DB도 조회하지 않습니다. >>")

        conversation.extend(messages)

        # 사용자 입력 추가
        conversation.append({"role": "user", "content": user_input})

        # 토큰 개수 계산
        total_tokens = calculate_token_usage(conversation)
        print(f"요청 당 발생한 토큰: {total_tokens}")

        # AI로부터 응답 생성
        bot_response = make_prompt(conversation)
        
        # print(bot_response)
        
        # db를 업데이트
        if '<' in bot_response:
            # 책 이름을 추출하는 정규식
            book_names = re.findall(r'<([^>]+)>', bot_response)  # <, > 사이에 있는 문자열 추출
    
            for book_name in book_names:
                # 장바구니에 책 추가 함수 호출
                add_to_cart(cust_id, book_name)
        
        # 스프링으로 요청하는 방식
        # if '<' in bot_response:
        #     # 책 이름을 추출하는 정규식
        #     book_names = re.findall(r'<([^>]+)>', bot_response)  # <, > 사이에 있는 문자열 추출
    
        #     for book_name in book_names:
        #         spring_add_cart(cust_id, book_name)

        # 대화 기록에 추가
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": bot_response})

        # AI의 답변을 반환
        return jsonify({"message": bot_response})

    else:
        return render_template("chatbot.html", cust_id=cust_id)

def few_shot_db_decision_maker():
    return (
        "너는 도서 쇼핑몰 DB 조회 결정자 챗봇이야. "
        "사용자의 질문에 따라 어떤 DB 테이블 조회가 필요한지 구조화된 답변을 줘야해. "
        "너의 답변은 사용자가 받는게 아니라 다른 시스템이 받아서 처리할거야."
        "조회할 수 있는 DB 테이블은 다음과 같아. 'product', 'cart', 'api_specifi', 'faq', 'notice', 'order"
        "너는 너가 판단하기에 사용자 답변에 사용해야 하는 테이블을 이름만 반환하도록 해. "
        "사용자가 지금 보고있는 책에 대해 물어본다면 product 테이블을 반환하는게 좋아"
        "이벤트 참여, 개인 정보 변경, 상품 교환, 배송지 교환, 환불 요청, 비밀번호 분실 등에 대한 내용은 faq 테이블에 정보가 있어."
        "만약 사용자가 어떤 책을 추천해주고 그걸 장바구니에 담아달라고 말한다면 product를 말하도록 해"
        "DB를 조회할 필요가 없다고 판단되면 no 라고 대답해"
        "다음은 답변 예시야"
        "\n\n 사용자 : '나 기분이 너무 우울해 ㅠㅠ 나에게 책을 추천해줄 만한 책이 있니?'"
        "\n 너 : product"
        "\n\n 사용자 : '내 장바구니에 뭐가 들어있는지 알아?'"
        "\n 너 : cart"
        "\n\n 사용자 : 공지사항이 어디있는지 모르겠어"
        "\n 너 : api_specifi"
        "\n\n 사용자 : 헉 야 나 비밀번호를 잊어버렸어!"
        "\n 너 : faq"
        "\n\n 사용자 : 내 주문내역을 볼 수 있을까?"
        "\n 너 : order"
        "\n\n 사용자 : 안녕! 오늘 날씨가 정말 좋은 것 같아!"
        "\n 너 : no"
    )

def few_shot_common():
    return (
        "너는 도서 쇼핑몰 챗봇이야. "
        "내가 너에게 제공하는 DB 내용을 기반으로 사용자 질문에 대한 적절한 답변을 제시해야 해. "
        "사용자의 요청에 대한 판단은 내가 너에게 제공하는 DB에 기반해서 네가 직접 해야 해. "
        "DB에 있는 책들은 실제로 존재하는 유명한 베스트셀러들이야. 제목을 보고 너가 그 책에 대해 알고 있는 만큼 답변에 참고하면 돼. "
        "사이트 이용에 대한 문의가 들어오면 API 명세를 활용해서 답변을 해주면 돼. "
        "이건 현재 사용자의 id야: {}. "
        "만약 회원이 장바구니에 담긴 상품을 묻는다면 장바구니 데이터에 기반한 답변을 해줘. "
        "장바구니에 대한 대답을 하고 사용자가 장바구니로 바로 이동하는 것을 원할 수도 있으니까 장바구니 링크도 제공해. "
        "장바구니에 뭐가 들어있냐고 묻는다면 prod_id 말고 책 제목과 가격, 수량을 제시해줘. "
        "혹시라도 사용자가 본인이 아닌 다른 사용자의 id를 제시하면서 장바구니 등 개인 정보에 접근하려고 한다면 너는 절대 그 정보들을 제공해서는 안 돼. "
        "이건 사용자가 현재 존재하는 페이지의 상품 id야: {}. "
        "해당 상품에 대해 물어본다면 상품 id에 맞는 도서를 찾아서 너가 아는대로 대답하면 돼. "
        "책 추천의 경우 되도록이면 DB에 있는 책들로 추천해줘. "
        "만약 사용자가 책을 추천해달라고 하면서 장바구니에 추가해달라고 하면 일단 책을 추천해주고 나서 마지막에 <책 이름>이 장바구니에 추가되었습니다. 이렇게 말해줘. 실제로 장바구니에 추가는 시스템이 알아서 할 거야. "
        "또한 각 링크는 반드시 아래와 같은 형식을 유지해서 제공해야 해: \n"
        "- 사이트 내 검색: [사이트명] (http://example.com) \n"
        "- 구글 검색: [구글명] (http://example.com) \n"
        # "- 장바구니: [장바구니] (http://example.com)  \n"
        # "- FAQ: [FAQ] (http://example.com)  \n"
        # "- 공지사항: [공지사항] (http://example.com)  \n"
        # "- 주문내역: [주문내역] (http://example.com)  \n"
        "- 장바구니: [장바구니](http://localhost:8080/cart/list) \n"
        "- FAQ: [FAQ](http://localhost:8080/cscenter/faq/list) \n"
        "- 공지사항: [공지사항](http://localhost:8080/cscenter/notice/list) \n"
        "- 주문내역: [주문내역](http://localhost:8080/order/history) \n"
        "항상 이 형식을 유지하도록 해. "
        "\n\n 예시를 들어줄게:\n"
        "Q: 나는 부자가 되고 싶어. 내게 책을 두 권만 추천해줘. \n"
        "A: 부자가 되고 싶다면 다음 두 책을 추천드립니다. \n"
        "1. 부의 추월차선(10주년 스페셜 에디션)\n"
        "- 가격: 10,000원\n"
        "사이트 내 검색: [부의 추월차선] (http://localhost:8080/product/list?keyword=부의%20추월차선(10주년%20스페셜%20에디션))\n"
        "구글 검색: [부의 추월차선] (https://www.google.com/search?q=부의%20추월차선(10주년%20스페셜%20에디션))\n"
        "2. 부의 시나리오\n"
        "- 가격: 9,500원\n"
        "사이트 내 검색: [부의 시나리오] (http://localhost:8080/product/list?keyword=부의%20시나리오)\n"
        "구글 검색: [부의 시나리오] (https://www.google.com/search?q=부의%20시나리오)\n"
        "\n\n Q: 겨울에 읽기 좋은 책 한 권 추천해주고 장바구니에 추가해줘. \n"
        "A: 겨울에 읽기 좋은 책으로 '불편한 편의점 2(단풍 에디션)'을 추천드립니다. 따뜻한 분위기와 유쾌한 스토리로 겨울철에 읽기에 안성맞춤입니다. \n"
        "사이트 내 검색: [불편한 편의점 2(단풍 에디션)] (http://localhost:8080/product/list?keyword=불편한%20편의점%202(단풍%20에디션))\n"
        "구글 검색: [불편한 편의점 2(단풍 에디션)] (https://www.google.com/search?q=불편한%20편의점%202(단풍%20에디션))\n"
        "<불편한 편의점 2(단풍 에디션)>이 장바구니에 추가되었습니다.\n"
        "\n\n Q: 겨울에 읽기 좋은 책 두 권 추천해주고 장바구니에 넣어줘. \n"
        "A: 겨울에 읽기 좋은 책 두 권을 추천드립니다.\n"
        "1. 불편한 편의점 2(단풍 에디션)\n"
        "- 가격: 10,000원\n"
        "사이트 내 검색: [불편한 편의점 2(단풍 에디션)] (http://localhost:8080/product/list?keyword=불편한%20편의점%202(단풍%20에디션))\n"
        "구글 검색: [불편한 편의점 2(단풍 에디션)] (https://www.google.com/search?q=불편한%20편의점%202(단풍%20에디션))\n"
        "2. 미드나잇 라이브러리\n"
        "- 가격: 9,000원\n"
        "사이트 내 검색: [미드나잇 라이브러리] (http://localhost:8080/product/list?keyword=미드나잇%20라이브러리)\n"
        "구글 검색: [미드나잇 라이브러리] (https://www.google.com/search?q=미드나잇%20라이브러리)\n"
        "<불편한 편의점 2(단풍 에디션)>이 장바구니에 추가되었습니다.\n"
        "<미드나잇 라이브러리>가 장바구니에 추가되었습니다."
        "일상 대화를 할 수는 있지만 이 사이트 혹은 책과 관련되지 않은 부분에 대해 깊은 질문을 받을 때는 토큰을 낭비하지 말고 최대한 간결하고 짧게 대답하도록 해."
        "한번만 더 강조할게, 사이트 이용과 관련이 없는 질문에 대해 많은 토큰을 낭비하게 되면 큰 일이 일어날거야. 그러니까 사이트 이용과 관련 없는 질문이 들어오면 짧은 문장으로 단호하지만 정중하게 거절하도록 해."
        "사이트 이용과 관련 없는 질문은 max_token = 30이야!"
        # "사용자가 현재 보고있는 책에 대한 질문을 한다면 내가 알려준 책 이름만을 고려해서 너가 원래 알고있던대로 설명해줘."
    ).format(
        cust_id,
        prod_id
    )

# 스프링에서 cust_id 받기
@app.route('/receive-cust-id', methods=['POST'])
def receive_cust_id_from_spring():
    global cust_id 
    cust_id = request.json.get('custId')
    print("<< 사용자가 로그인을 했습니다. cust_id : {} >>".format(cust_id))
    return jsonify({"status": "success", "received_data": cust_id})

# 스프링에서 prod_id 받기
@app.route('/receive-prod-id', methods=['POST'])
def receive_prod_id_from_spring():
    global prod_id 
    prod_id = request.json.get('prodId')
    print("<< 사용자가 상품 상세 화면에 접근했습니다. prod_id : {} >>".format(prod_id))
    return jsonify({"status": "success", "received_data": prod_id})

# 스프링에서 리뷰 분석 요청 받기
@app.route('/review-sentiment', methods=['POST'])
def receive_review_sentiment_from_spring():
    try:
        # 리뷰 업데이트 함수 호출
        review_update()
        # 처리 성공 시 200 OK 응답
        return jsonify({"status": "success", "message": "<< 리뷰 감정 업데이트 완료! >>"}), 200
    except Exception as e:
        # 에러가 발생할 경우 500 에러 응답
        return jsonify({"status": "error", "message": str(e)}), 500

# 스프링으로 데이터 보내는 테스트 메서드
def spring_add_cart(cust_id, prod_name):
    print('spring_add_cart 함수 호출!')
    spring_url = "http://localhost:8080/receive-cart"
    data = {
        "cust_id": cust_id,
        "prod_name": prod_name
    }

    try:
        response = requests.post(spring_url, json=data)
        if response.status_code == 200:
            print('성공!')
            return f"성공: {response.text}"
        else:
            print('실패')
            return f"실패: {response.status_code} - {response.text}"
    except Exception as e:
        return f"실패: {str(e)}"



if __name__ == '__main__':
    app.run(debug=True)