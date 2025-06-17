# from django.contrib import admin
# from .models import Message


# @admin.register(Message)
# class MessageAdmin(admin.ModelAdmin):
#     list_display = ("sender", "receiver", "subject", "is_read", "created_at")
#     list_filter = ("is_read", "created_at")
#     search_fields = ("sender__email", "receiver__email", "subject", "content")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-created_at",)

#     fieldsets = (
#         ("Message Details", {"fields": ("sender", "receiver", "subject", "content")}),
#         ("Status", {"fields": ("is_read", "read_at")}),
#         (
#             "Timestamps",
#             {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
#         ),
#     )


# # @admin.register(Conversation)
# # class ConversationAdmin(admin.ModelAdmin):
# #     list_display = ('id', 'get_participants', 'last_message_at', 'created_at')
# #     list_filter = ('created_at', 'last_message_at')
# #     search_fields = ('participants__email',)
# #     readonly_fields = ('created_at', 'updated_at')

# #     def get_participants(self, obj):
# #         return ", ".join([user.email for user in obj.participants.all()])
# #     get_participants.short_description = 'Participants'
