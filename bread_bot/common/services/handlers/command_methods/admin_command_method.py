from sqlalchemy import and_

from bread_bot.common.exceptions.base import RaiseUpException, NextStepException
from bread_bot.common.models import (
    AnswerPack,
    TextEntity,
    VoiceEntity,
    PhotoEntity,
    StickerEntity,
    GifEntity,
    VideoEntity,
    VideoNoteEntity,
)
from bread_bot.common.schemas.bread_bot_answers import TextAnswerSchema
from bread_bot.common.schemas.commands import (
    CommandSchema,
    KeyValueParameterCommandSchema,
    ValueCommandSchema,
    ValueParameterCommandSchema,
)
from bread_bot.common.services.handlers.command_methods.base_command_method import BaseCommandMethod
from bread_bot.common.utils.structs import (
    AdminCommandsEnum,
    ANSWER_ENTITY_MAP,
    AnswerEntityTypesEnum,
)


class AdminCommandMethod(BaseCommandMethod):
    async def execute(self) -> TextAnswerSchema:
        match self.command_instance.command:
            case AdminCommandsEnum.ADD:
                return await self.add(
                    key=self.command_instance.key,
                    value=self.command_instance.value,
                    entity_class=TextEntity,
                    reaction_type=ANSWER_ENTITY_MAP[self.command_instance.parameter],
                )
            case AdminCommandsEnum.SHOW:
                return await self.show()
            case AdminCommandsEnum.REMEMBER:
                return await self.remember(reaction_type=AnswerEntityTypesEnum.SUBSTRING)
            case AdminCommandsEnum.REMEMBER_TRIGGER:
                return await self.remember(reaction_type=AnswerEntityTypesEnum.TRIGGER)
            case AdminCommandsEnum.DELETE:
                return await self.delete()
            case AdminCommandsEnum.ANSWER_CHANCE:
                return await self.handle_answer_chance()
            case _:
                raise NextStepException("Не найдена команда")

    async def show(self):
        raise RaiseUpException("Функция временно отключена")

    async def add(
        self,
        key: str,
        value: str,
        entity_class: any,
        reaction_type: AnswerEntityTypesEnum,
        description: str | None = None,
    ):
        """Команда Добавить"""
        self._check_length_key(reaction_type, key)

        answer_pack: AnswerPack = await AnswerPack.get_by_chat_id(self.db, self.member_service.chat.id)

        if not answer_pack:
            answer_pack: AnswerPack = await AnswerPack.create_by_chat_id(self.db, self.member_service.chat.id)
        entity = await entity_class.async_first(
            self.db,
            where=and_(
                entity_class.key == key.lower(),
                entity_class.value == value,
                entity_class.pack_id == answer_pack.id,
                entity_class.reaction_type == reaction_type,
            ),
            for_update=True,
        )
        if entity is None:
            instance_params = dict(
                pack_id=answer_pack.id,
                key=key.lower(),
                value=value,
                reaction_type=reaction_type,
            )
            if description is not None:
                instance_params.update(dict(description=description))
            await entity_class.async_add(db=self.db, instance=entity_class(**instance_params))
        return self._return_answer()

    async def remember(self, reaction_type: AnswerEntityTypesEnum = AnswerEntityTypesEnum.SUBSTRING):
        """Команда Запомни"""
        self._check_reply_existed()
        reply = self.message_service.message.reply
        description: str | None = None

        if reply.voice:
            value = reply.voice.file_id
            entity_class = VoiceEntity
        elif reply.photo:
            value = reply.photo[0].file_id
            entity_class = PhotoEntity
            description = reply.caption
        elif reply.sticker:
            value = reply.sticker.file_id
            entity_class = StickerEntity
        elif reply.video:
            value = reply.video.file_id
            entity_class = VideoEntity
        elif reply.video_note:
            value = reply.video_note.file_id
            entity_class = VideoNoteEntity
        elif reply.animation:
            value = reply.animation.file_id
            entity_class = GifEntity
        elif reply.text:
            value = reply.text
            entity_class = TextEntity
        else:
            raise RaiseUpException("Данный тип данных не поддерживается")
        for key in self.command_instance.value_list:
            await self.add(
                key=key,
                value=value,
                entity_class=entity_class,
                reaction_type=reaction_type,
                description=description,
            )
        return self._return_answer()

    async def delete(self):
        """Удаление по ключам и по ключам-значениям"""
        answer_pack: AnswerPack = await AnswerPack.get_by_chat_id(
            db=self.db,
            chat_id=self.member_service.chat.id,
        )
        if answer_pack is None:
            return self._return_answer("У чата нет ни одного пакета под управлением")

        for entity_class in (
            TextEntity,
            VoiceEntity,
            PhotoEntity,
            StickerEntity,
            GifEntity,
            VideoEntity,
            VideoNoteEntity,
        ):
            match self.command_instance:
                case KeyValueParameterCommandSchema():
                    await entity_class.async_delete(
                        self.db,
                        where=and_(
                            entity_class.key == self.command_instance.key,
                            entity_class.value == self.command_instance.value,
                            entity_class.pack_id == answer_pack.id,
                            entity_class.reaction_type == ANSWER_ENTITY_MAP[self.command_instance.parameter],
                        ),
                    )
                case ValueParameterCommandSchema():
                    await entity_class.async_delete(
                        self.db,
                        where=and_(
                            entity_class.key == self.command_instance.value,
                            entity_class.pack_id == answer_pack.id,
                            entity_class.reaction_type == ANSWER_ENTITY_MAP[self.command_instance.parameter],
                        ),
                    )
                case _:
                    raise RaiseUpException("Введены неправильные значения")
        return self._return_answer()

    async def handle_answer_chance(self):
        answer_pack: AnswerPack = await AnswerPack.get_by_chat_id(
            db=self.db,
            chat_id=self.member_service.chat.id,
        )
        if not answer_pack:
            answer_pack: AnswerPack = await AnswerPack.create_by_chat_id(self.db, self.member_service.chat.id)
        match self.command_instance:
            case ValueCommandSchema():
                chance_value = self.command_instance.value
                error_message = "Некорректное значение. Необходимо ввести число от 0 до 100"
                try:
                    value = int(chance_value.strip())
                except (ValueError, AttributeError):
                    return self._return_answer(error_message)
                if value > 100 or value < 0:
                    return self._return_answer(error_message)
                answer_pack.answer_chance = value
                await AnswerPack.async_add(db=self.db, instance=answer_pack)
                return self._return_answer()
            case CommandSchema():
                return self._return_answer(str(answer_pack.answer_chance))
            case _:
                raise RaiseUpException("Не удалось установить процент срабатывания")