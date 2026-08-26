"""Identity types.

Opaque to the domain: only the persistence adapter knows these are database integers.
"""

from typing import NewType

UserId = NewType("UserId", int)
PostId = NewType("PostId", int)
EngagementId = NewType("EngagementId", int)
FeedbackId = NewType("FeedbackId", int)
ContactMessageId = NewType("ContactMessageId", int)
OTPId = NewType("OTPId", int)
ModerationLogId = NewType("ModerationLogId", int)
