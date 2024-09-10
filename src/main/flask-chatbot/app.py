import tiktoken
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
from database import get_product, get_cart, get_FAQ, get_notice, get_QNA
from api_specifi import get_api_routes
from review_sentiment import eval_sentiment
from review_sentiment import review_update

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
        model='gpt-4o',
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
            cart_data = get_cart(cust_id)
            conversation.append(
                {"role": "system", "content": f"이건 사용자의 장바구니 데이터야: {cart_data}"}
            )
        elif db_to_query == "product":
            print("<< 챗봇이 상품 테이블을 조회합니다. >>")
            product_data = get_product()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 상품 데이터야: {product_data}"}
            )
        elif db_to_query == "api_specifi":
            print("챗봇이 api 명세를 조회합니다.")
            faq_data = get_api_routes()
            conversation.append(
                {"role": "system", "content": f"이건 쇼핑몰의 api 명세야: {faq_data}"}
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
        "조회할 수 있는 DB 테이블 'product', 'cart', 'api_specifi'가 있어."
        "너는 너가 판단하기에 사용자 답변에 사용해야 하는 테이블을 이름만 반환하도록 해. "
        "DB를 조회할 필요가 없다고 판단되면 no 라고 대답해"
        "다음은 답변 예시야"
        "\n\n 사용자 : '나 기분이 너무 우울해 ㅠㅠ 나에게 책을 추천해줄 만한 책이 있니?'"
        "\n 너 : product"
        "\n\n 사용자 : '내 장바구니에 뭐가 들어있는지 알아?'"
        "\n 너 : cart"
        "\n\n 사용자 : 공지사항이 어디있는지 모르겠어"
        "\n 너 : api_specifi"
        "\n\n 사용자 : 안녕! 오늘 날씨가 정말 좋은 것 같아!"
        "\n 너 : no"
    )

def few_shot_common():
    return (
        "너는 도서 쇼핑몰 챗봇이야. "
        "내가 너에게 제공하는 DB 내용을 기반으로 사용자 질문에 대한 적절한 답변을 제시해야 해. "
        "사용자의 요청에 대한 판단은 내가 너에게 제공하는 DB에 기반해서 네가 직접 해야 해. "
        "DB에 있는 책들은 실제로 존재하는 유명한 베스트셀러들이야. 제목을 보고 너가 그 책에 대해 이미 알고있는 만큼 답벼에 참고하면 될거야."
        "사이트 이용에 대한 문의가 들어오면 api 명세를 활용해서 답변을 해주면 돼. "
        "이건 현재 사용자의 id야: {}. "
        "만약 회원이 장바구니에 담긴 상품을 묻는다면 사용자 id와 장바구니 table의 cust_id가 일치하는 품목들에 대해 답변을 해줘야 해. "
        "장바구니에 대한 대답을 하고 사용자가 장바구니로 바로 이동하는 것을 원할수도 있으니까 장바구니 링크도 제공해"
        "혹시라도 사용자가 본인이 아닌 다른 사용자의 id를 제시하면서 장바구니 등 개인 정보에 접근하려고 한다면 너는 절대 그 정보들을 제공해서는 안 돼."
        "이건 사용자가 현재 존재하는 페이지의 상품 id야: {}"
        "해당 상품에 대해 물어본다면 상품 id에 맞는 도서를 찾아서 너가 아는대로 대답하면 돼."
        "한번 더 얘기하지만, 상품들은 모두 실제로 존재하는 유명한 책들이라서 너가 알고있는 만큼 대답하면 돼."
        "지금부터는 예측되는 사용자 질문에 대한 답변 가이드를 너에게 제시할 거야. "
        "잘 참고해서 실제 답변에 활용하길 바랄게. "
        "책 추천의 경우 되도록이면 DB내 존재하는 책들로 추천해줘. "
        "되도록이면 DB에 있는 책들로 추천했으면 좋겠지만, 너가 아무리 생각해도 DB에 추천할만한 책이 없으면 너가 알고있는 다른 유명한 책으로 추천하고 구글 링크만 제공해"
        "\n\n Q: 나는 부자가 되고싶어! 내게 책을 두 권만 추천해줘\n"
        "부자가 되고 싶다면 다음 두 책을 추천합니다.\n"
        "- 부의 추월차선(10주년 스페셜 에디션)\n"
        "사이트 내 검색: http://localhost:8080/product/list?keyword=추월차선(10주년%20스페셜%20에디션)\n"
        "구글 검색: https://www.google.com/search?q=추월차선(10주년%20스페셜%20에디션)\n"
        "\n"
        "- 부의 시나리오\n"
        "사이트 내 검색: http://localhost:8080/product/list?keyword=부의%20시나리오\n"
        "구글 검색: https://www.google.com/search?q=부의%20시나리오\n"
        "\n\n 이 형식을 꼭 지켜야만 해. 시스템은 너의 답변 형식을 인지해서 링크를 버튼으로 제공하는 기능이 있거든."
        "가격을 조건으로 추천 질문이 들어오면 대답에 가격 정보도 표시하도록 해."
        "답변할때 줄바꿈에 신경좀 많이 써줘. 한 문장 이후 줄바꿈, 가격 알려주기 전에 줄바꿈, 링크 제공하기 전에 줄바꿈 이런 느낌으로. "
        "\n\n product 테이블의 ord_chk_code는 AVBL일 경우 판매가능 OSKT는 일시품절 STOP은 판매중지야. "
        "레코드의 개별적인 정보에 대해서는 제공할 필요 없어 이를테면 ' - 새벽배송 여부: **Y** - 판매 상태: **AVBL** ' 이런거 답변에 포함하지 말라는거야. "
        "너가 답변을 마크다운 형식으로 하는 경향이 있는 것 같아. 답변을 마크다운 형식으로 주지 말되 줄바꿈은 신경써서 해줘."
        "\n\nAPI 명세 기반으로 링크를 제공할 때는 'http://localhost:8080'이 앞에 붙어야 해"
        "유사한 상황에 대한 답변 가이드를 줄게 다음과 같아."
        "\n Q: 공지사항이 대체 어디있는거야?"
        "A: 공지사항 이용을 위해서 다음 링크로 이동하세요 'http://localhost:8080/cscenter/notice/list'\n\n"
        "일상 대화를 할 수는 있지만 이 사이트 혹은 책과 관련되지 않은 부분에 대해 깊은 질문을 받을 때는 토큰을 낭비하지 말고 최대한 간결하고 짧게 대답하도록 해."
        "한번만 더 강조할게, 사이트 이용과 관련이 없는 질문에 대해 많은 토큰을 낭비하게 되면 큰 일이 일어날거야. 그러니까 사이트 이용과 관련 없는 질문이 들어오면 짧은 문장으로 단호하지만 정중하게 거절하도록 해."
        "사이트 이용과 관련 없는 질문은 max_token = 30이야!"
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

if __name__ == '__main__':
    app.run(debug=True)