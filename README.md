# 📌 쇼핑몰 프로젝트
### 주제
- 프로젝트명: 정석문고
- 스프링을 통한 쇼핑몰 기본 기능 구현
- 프로젝트 기간: 2024/08/05 ~ 2024/08/19

### 벤치마킹사이트
- [교보문고](https://www.kyobobook.co.kr/)

### 개발 환경
- Java -17
- SpringBoot - 3.3.2
- Mybatis - 3.5.9
- Tomcat - 9.0.91
- DB: MySql 8.0
- Junit - 5.10.3

### 역할
- 강영웅: 회원가입/로그인
- 이의준: 상품/카테고리
- 오승민: 장바구니
- 한지선: 주문/결제
- 김진우: 게시판(공지사항, FAQ, 고객문의)

## 📌 설계
### 화면 정의서
- [1조_화면정의서]
- [1조_화면 정의서.pptx](https://github.com/user-attachments/files/16655691/1._.pptx)

### DB 모델링
- [1조 ERD]
- ![1조_ERD](https://github.com/user-attachments/assets/6cd6ec47-c8ad-4ea6-a00e-e6c43415db75)

### API 명세
- [1조 API 명세서]
- ![1조_API명세서](https://github.com/user-attachments/assets/ad06578c-d9e3-42d8-a4d4-e12916ccc063)

<br>

***
***

<br>

# 📌 챗봇 프로젝트 - 담당 : 이의준

### 주제
- 프로젝트명: 쇼핑몰 챗봇 기능 구현
- 프로젝트 기간: 2024/09/02 ~ 2024/09/13

## 개발환경
- [ 웹 ]
- Java - 17
- SpringBoot - 3.3.2
- Mybatis - 3.5.9
- Tomcat - 9.0.91
- DB : MySql 8.0
- Junit - 5.10.3

### [ 챗봇 ]
- Python - 3.12.5
- Flask - 3.0.3

-----------

## 사용 포트
- Spring tomcat : 8080
- Python : flask : 5000

-----------

## 구현 기능

1. 챗봇
- 쇼핑몰 이용 관련된 모든 질문에 대해 쇼핑몰 DB에 기반하는 답변을 제공함
- 텍스트로 답변하는 것 뿐만 아니라 버튼으로 바로가기 기능 제공, 장바구니에 담아주기 등 기능도 구현함

2. 리뷰 감정분석
- 작성된 리뷰들에 대해 관리자 페이지에서 분석 실행 버튼을 누르는 것으로 리뷰 데이터를 긍정/부정으로 예측
- 예측된 데이터를 통해 상품별로 구매자 반응을 비율로 제시

3. 상품 요약 번역 기능
- 상품 상세페이지에서 버튼 클릭시 요약 정보를 영어로 번역

---------

## 기타 링크
- [발표자료(Gamma)](https://gamma.app/docs/ToyProject-3-h9ilx5of589d6up)
- [시연영상(GoogleDrive)](https://drive.google.com/drive/folders/1YlBQdHelUarTYEgdIHRX-Ml70O_tOebM?usp=sharing)

