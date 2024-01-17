
import json
import os
import plugins
from bridge.reply import Reply, ReplyType
from bridge.context import ContextType
from plugins import *
from common.log import logger
from medisearch_client import MediSearchClient
import uuid

@plugins.register(
    name="seek1assit",
    desire_priority=2,
    desc="A plugin for seek one assit about medical problems",
    version="0.0.1",
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
            # 初始化成功日志
            logger.info("[seek1assit] inited.")
        except Exception as e:
            # 初始化失败日志
            logger.warn(f"seek1assit init failed: {e}")
    def on_handle_context(self, e_context: EventContext):
        context = e_context["context"]
        if context.type not in [ContextType.TEXT]:
            return
        content = context.content
        if content.startswith(self.prefix):
            self.handle_medi (content, e_context)
            return
    def handle_medi(self, content, e_context):
        api_key = self.medisearch_key
        conversation_id = str(uuid.uuid4())
        client = MediSearchClient(api_key=api_key)
        responses = client.send_user_message(conversation=[content], 
                                            conversation_id=conversation_id,
                                            should_stream_response=True,
                                            language="Chinese")

        llm_answer = None
        for response in responses:
            if response["event"] == "llm_response":
                llm_answer = response["text"]
                break

        if llm_answer is not None:
            reply_content = llm_answer
        else:
            content = "Content not found or error in response"
        except requests.exceptions.RequestException as e:
        # 处理可能出现的错误
            logger.error(f"Error calling: {e}")

        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content=reply.content
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
    def get_help_text(self, **kwargs):
        help_text = "解答医学方面的问题\n"
        return help_text