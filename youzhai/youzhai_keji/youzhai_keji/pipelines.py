# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import logging
logger = logging.getLogger(__name__)


class YouzhaiKejiPipeline(object):

    def process_item(self, item, spider):
        logger.info(item)
        with open("tianyan.json", "w") as f:
            f.write(json.dumps(dict(item), ensure_ascii=False, indent=2))

        return item


