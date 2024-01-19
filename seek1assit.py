
import json
import os
import plugins
import requests
from bridge.reply import Reply, ReplyType
from plugins import Plugin, Event, EventContext, EventAction
from common.log import logger
from medisearch_client import MediSearchClient
import uuid
import re

@plugins.register(
    name="seek1assit",
    desire_priority=2,
    desc="A plugin for seek one assit about medical problems",
    version="0.0.2",
    author="fatwang2",
)
class seek1assit(Plugin):
    def __init__(self):
        super().__init__()
        try:
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                # 使用父类的方法来加载配置
                self.config = super().load_config()
                if not self.config:
                    raise Exception("config.json not found")
            # 设置事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            # 从配置中提取所需的设置
            self.medisearch_key = self.config.get("medisearch_key", {})
            self.prefix = self.config.get("prefix", {})
            self.show_details = self.config.get("show_details", False)
            # 初始化成功日志
            logger.info("[seek1assit] inited.")
        except Exception as e:
            # 初始化失败日志
            logger.warn(f"seek1assit init failed: {e}")
    def on_handle_context(self, e_context: EventContext):
        content = e_context["context"].content
        if content.startswith(self.prefix):
            self.handle_medi (content, e_context)
            return
    def handle_medi(self, content, e_context):
        try:
            api_key = self.medisearch_key
            conversation_id = str(uuid.uuid4())
            client = MediSearchClient(api_key=api_key)
            responses = client.send_user_message(conversation=[content], 
                                                conversation_id=conversation_id,
                                                should_stream_response=False,
                                                language="Chinese")

            llm_answer = None
            articles = []

            for response in responses:
                if response["event"] == "llm_response":
                    llm_answer = response["text"]
                elif response["event"] == "articles" and self.show_details == True:
                    for i, article in enumerate(response["articles"]):
                        authors = ", ".join(article["authors"])
                        year = "(" + article["year"] + ")"
                        url = self.short_url(article["url"])
                        if url is None:
                            url = article["url"]
                        articles.append(f"{i+1}. {authors} {year}：{url}")

            if llm_answer is not None:
                if self.show_details == False:
                    llm_answer = re.sub(r'\[\d+\]', '', llm_answer)
                reply_content = llm_answer
                if articles:
                    reply_content += "\n\n参考资料：\n" + "\n".join(articles)
            else:
                reply_content = "Content not found or error in response"

        except requests.exceptions.RequestException as e:
            # 处理可能出现的错误
            logger.error(f"Error calling: {e}")
            reply_content = "An error occurred while processing the request"

        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = reply_content  
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
    def short_url(self, long_url):
        url = "https://short.fatwang2.com"
        payload = {
            "url": long_url
        }        
        headers = {'Content-Type': "application/json"}
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code == 200:
            res_data = response.json()
            # 直接从返回的 JSON 中获取短链接
            short_url = res_data.get('shorturl', None)  
            if short_url:
                return short_url
        return None
    def get_help_text(self, **kwargs):
        help_text = "专业解答医学问题\n"
        return help_text