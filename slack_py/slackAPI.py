# -*- coding: utf-8 -*-

from flask import Flask, request
from slack_sdk import WebClient
import re
import sys
import jenkins
import time
import requests

# Jenkins 서버 URL 및 자격 증명 설정
jenkins_url = 'http://localhost:8080'
username = 'admin'
password = 'test123'

# Jenkins 객체 생성
server = jenkins.Jenkins(jenkins_url, username=username, password=password)

app = Flask(__name__)

class SlackAPI:
    """
    슬랙 API 핸들러
    """
    def __init__(self, token):
        self.client = WebClient(token)
        
    def get_channel_id(self, channel_name):
        """
        슬랙 채널ID 조회
        """
        result = self.client.conversations_list()
        channels = result.data['channels']
        filtered_channels = list(filter(lambda c: c["name"] == channel_name, channels))
        if filtered_channels:
            channel = filtered_channels[0]
            # 채널ID 파싱
            channel_id = channel["id"]
            return channel_id
        else:
            print(f"Channel '{channel_name}' not found. Shut down the server.")
            sys.exit(1)  # 서버 종료, 종료 코드 1 반환

    def get_latest_message(self, channel_id):
        """
        슬랙 채널 내 메세지 조회
        """
        # conversations_history() 메서드 호출
        result = self.client.conversations_history(channel=channel_id)

        # 채널 내 메세지 정보 딕셔너리 리스트
        messages = result.data['messages']

        # 마지막 메세지
        message = messages[0]

        msg = None

        # github 커밋 메세지일 때
        if 'bot_id' in message and message['bot_id'] == 'B06RCGCUJQN':
            text = message['attachments'][0]['fallback']

            # 정규 표현식 패턴
            pattern = r'\[(.*?)\:(.*?)\]'
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if match[0] == 'myReact':
                        msg = "🚀 프론트엔드에서 새로운 커밋이 발생하였습니다. \n 배포를 원하실 경우 '프론트엔드 배포'라고 입력해주세요!"
                    elif match[0] == 'backKakao':
                        msg = "🚀 백엔드에서 새로운 커밋이 발생하였습니다. \n 배포를 원하실 경우 '백엔드 배포'라고 입력해주세요!"
                    else:
                        print(f"This is not a commit message. Shut down the server.")
                        sys.exit(1)  # 서버 종료, 종료 코드 1 반환
            else: 
                print(f"This is not a commit message. Shut down the server.")
                sys.exit(1)  # 서버 종료, 종료 코드 1 반환

        # 프론트엔드 배포 메세지일 때
        elif 'text' in message and message['text'] == '프론트엔드 배포':
            self.post_message("C06R4JFPHPH", "🚀 프론트엔드 배포를 시작합니다.")
            # Jenkins 작업 가져오기
            job_name = 'myWeb'
            # 작업 빌드
            server.build_job(job_name)

            self.get_build_console_output(jenkins_url, job_name, username, password)

            msg = "🎉 프론트엔드 배포가 성공적으로 완료되었습니다!"

        
        # 백엔드 배포 메세지일 때
        elif 'text' in message and message['text'] == '백엔드 배포':
            msg = "🚀 백엔드 배포를 시작합니다."
            msg ="백엔드배포 완료"

        return msg

    def post_message(self, channel_id, msg):
        """
        슬랙 채널에 메세지 보내기
        """
        # chat_postMessage() 메서드 호출
        result = self.client.chat_postMessage(channel=channel_id, text=msg)
        return result

    # Jenkins 서버 API로 빌드 중인 작업의 콘솔 출력 가져오기
    def get_build_console_output(self, server_url, job_name, username, password):
        url = f"{server_url}/job/{job_name}/lastBuild/logText/progressiveText"
        headers = {'Accept': 'text/plain'}
        session = requests.Session()
        session.auth = (username, password)
        
        try:
            while True:
                response = session.get(url, headers=headers, stream=True, timeout=10)
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        # print(line)
                        if line.strip().startswith("+ git pull"):
                            self.post_message("C06R4JFPHPH", "> 새로운 커밋 적용")
                        elif line.strip().startswith("+ sudo docker build"):
                            self.post_message("C06R4JFPHPH", "> 이미지 빌드 중 ...")
                        elif line.strip().startswith("+ sudo docker push"):
                            self.post_message("C06R4JFPHPH", "> 이미지 푸시 중 ...")
                        elif line.strip().startswith("+ ansible"):
                            self.post_message("C06R4JFPHPH", "> 배포 중 ...")
                        elif line.strip() == "Finished: SUCCESS":
                            return  # 빌드가 성공적으로 완료되면 함수 종료
        except requests.exceptions.Timeout:
            print("Timeout occurred. Retrying...")
            get_build_console_output(server_url, job_name, username, password)
        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)

def send_message_periodically():
    while True:
        # SlackAPI 인스턴스를 만듭니다.
        slack_api = SlackAPI(token='비밀')
        
        # 채널 이름
        # channel_name = "cicd"
        
        # 채널 ID 파싱
        # channel_id = slack_api.get_channel_id(channel_name)
        channel_id = "C06R4JFPHPH"
        
        # 메시지 파싱
        msg = slack_api.get_latest_message(channel_id)

        time.sleep(5)

        # 메세지 전송
        if msg != None:
            slack_api.post_message(channel_id, msg)


send_message_periodically()

@app.route('/slack/message', methods=['POST'])
def handle_message():
    # 슬랙에서의 요청을 받습니다.
    data = request.json
    # 요청에 대한 응답을 반환합니다.
    return 'Message handled successfully!', 200


if __name__ == '__main__':
    app.run(debug=True)
