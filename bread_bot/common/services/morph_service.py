import math
import random
import re
from typing import Any

import pymorphy2
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from bread_bot.common.exceptions.base import RaiseUpException
from bread_bot.common.models import DictionaryEntity

morph = pymorphy2.MorphAnalyzer()


class MorphService:
    def __init__(self, db: AsyncSession, chat_id: int):
        self.db: AsyncSession = db
        self.chat_id: int = chat_id

    @classmethod
    def _get_tags(cls, morph_word) -> tuple:
        morph_tag = morph_word.tag
        return (
            morph_tag.POS,
            morph_tag.case,
            morph_tag.number,
            morph_tag.gender,
            morph_tag.tense,
            morph_tag.person,
        )

    @classmethod
    def _get_maximum_words_to_replace(cls, words_count: int) -> int:
        if words_count == 1:
            coefficient = 1
        elif words_count == 2:
            coefficient = 0.5
        else:
            coefficient = 0.3
        return math.ceil(words_count * coefficient)

    async def _get_dictionary_words(self) -> dict[tuple, Any]:
        entities = await DictionaryEntity.async_filter(self.db, DictionaryEntity.chat_id == self.chat_id)
        result = {}
        for entity in entities:
            parsed_word = morph.parse(entity.value)[0]
            for item in parsed_word.lexeme:
                key = self._get_tags(item)
                if key in result:
                    result[key].append(item.word)
                else:
                    result[key] = [item.word]
        return result

    async def morph_text(self, text: str) -> str:
        words = re.split(" ", text)
        words_count = len(words)
        dictionary_words = await self._get_dictionary_words()
        if not dictionary_words:
            raise RaiseUpException(
                "Словарь пуст. Пополните словарь командой:\n'Хлеб добавь бред слово1, слово2, "
                "слово3'\n\nПосле добавления текст начнет гибко меняться на добавленные слова"
            )
        for word_index in range(0, self._get_maximum_words_to_replace(words_count)):
            random_word_index = random.randint(0, words_count - 1)
            if words[random_word_index] == "\n":
                continue
            item = morph.parse(words[random_word_index])[0]
            key = self._get_tags(item)
            if key[0] is None:
                continue
            if key in dictionary_words:
                words[random_word_index] = random.choice(dictionary_words[key])
        return " ".join(words)

    async def add_values(self, values: list[str]):
        existed_dictionary_entities = await DictionaryEntity.async_filter(
            self.db, and_(DictionaryEntity.chat_id == self.chat_id, DictionaryEntity.value.in_(values))
        )
        existed_values = set([item.value for item in existed_dictionary_entities])
        to_create_entities = []
        for value in values:
            if value in existed_values:
                continue
            to_create_entities.append(
                DictionaryEntity(
                    chat_id=self.chat_id,
                    value=value,
                )
            )
        await DictionaryEntity.async_add_all(self.db, to_create_entities)

    async def delete_value(self, value: str):
        await DictionaryEntity.async_delete(
            self.db, and_(DictionaryEntity.chat_id == self.chat_id, DictionaryEntity.value == value)
        )

    async def morph_word(self, word: str, debug: bool = False) -> str:
        result = []
        parsed_word = morph.parse(word)[0]
        for item in parsed_word.lexeme:
            if debug:
                result.append(f"{str(item.tag)}: {item.word}")
            else:
                result.append(item.word)
        if debug:
            return "\n".join(result)
        else:
            return ", ".join(result)

    async def show_values(self) -> str:
        existed_dictionary_entities = await DictionaryEntity.async_filter(
            self.db, DictionaryEntity.chat_id == self.chat_id
        )
        return ", ".join([item.value for item in existed_dictionary_entities])