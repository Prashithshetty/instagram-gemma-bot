from abc import ABC, abstractmethod

class BasePlatformAdapter(ABC):
    """Abstract base class for a browser messaging platform."""

    def __init__(self, page):
        self.page = page

    def is_chat_open(self) -> bool:
        """Returns True if a conversation thread is currently open."""
        return True

    @abstractmethod
    def open_chat(self, target_user: str) -> bool:
        """Navigates to the specified user or opens their conversation."""
        pass

    @abstractmethod
    def get_messages(self):
        """Extract recent messages: [{'text': str, 'is_me': bool}]."""
        pass

    @abstractmethod
    def send_message(self, text: str) -> bool:
        """Types and sends a message into the active conversation."""
        pass

    @abstractmethod
    def get_chat_title(self) -> str:
        """Returns the name/title of the active conversation."""
        pass
