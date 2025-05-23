# news_analyzer/ui/import_export_dialog.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
导入/导出新闻批次对话框 UI 模块
"""

import os
import json
import logging
import re
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QComboBox, QFrame, QMessageBox, QFileDialog, QWidget) # Use PySide6, add QWidget if needed
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal # Import Signal for custom signals
from PySide6.QtCore import QSettings # <-- ADDED IMPORT

# 假设 NewsStorage 可以通过某种方式传入或访问
# from ..storage.news_storage import NewsStorage # 调整导入路径
from .ui_utils import create_separator, setup_combobox # 导入新的辅助函数

class ImportExportDialog(QDialog):
    """导入/导出新闻批次对话框"""

    # closed_and_deleted = pyqtSignal() # REMOVED unused signal

    def __init__(self, app_service, parent=None): # 接收 app_service 对象
        super().__init__(parent)
        self.logger = logging.getLogger('news_analyzer.ui.import_export_dialog')
        self.app_service = app_service
        self.settings = QSettings()
        # Get storage path from AppService's storage component
        if not hasattr(self.app_service, 'storage') or not hasattr(self.app_service.storage, 'data_dir'):
            self.logger.error("AppService or its storage lacks 'data_dir'. Cannot determine news directory.")
            QMessageBox.critical(self, "错误", "无法确定数据目录路径。导入/导出功能不可用。")
            # Disable relevant UI elements or close dialog
            # For now, just log and show message. Path will be incorrect.
            self.news_dir = "." # Fallback, likely incorrect
            self.analysis_dir = "."
        else:
            self.storage = self.app_service.storage # Keep reference if needed elsewhere
            # self.news_dir = os.path.join(self.storage.data_dir, "news") # Old incorrect access
            self.news_dir = os.path.join(self.app_service.storage.data_dir, "news")
            self.analysis_dir = os.path.join(self.app_service.storage.data_dir, "analysis")

        self.logger.info(f"Import/Export paths set: News='{self.news_dir}', Analysis='{self.analysis_dir}'")

        self._setup_ui()
        self._refresh_export_combo() # 初始化时刷新下拉列表

    def _setup_ui(self):
        """初始化对话框 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15) # 调整边距
        layout.setSpacing(15) # 增加间距

        # 添加说明文字
        instr_label = QLabel("在此页面中，您可以导入外部JSON新闻文件或导出现有的历史新闻批次文件。")
        instr_label.setWordWrap(True)
        instr_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(instr_label)

        # --- 导入部分 ---
        import_title = QLabel("导入JSON新闻文件")
        import_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #1976D2; margin-top: 10px;")
        layout.addWidget(import_title)

        import_desc = QLabel("选择一个JSON文件导入到系统。文件应包含新闻条目列表，将作为新的历史批次保存。")
        import_desc.setWordWrap(True)
        layout.addWidget(import_desc)

        self.import_json_button = QPushButton("选择并导入JSON文件")
        self.import_json_button.setObjectName("importJsonButton")
        self.import_json_button.clicked.connect(self._import_news_file)
        layout.addWidget(self.import_json_button)

        # 使用辅助函数创建分隔线
        separator = create_separator() # 调用辅助函数
        layout.addWidget(separator)

        # --- 导出部分 ---
        export_title = QLabel("导出历史新闻批次")
        export_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #1976D2;")
        layout.addWidget(export_title)

        export_desc = QLabel("选择并导出系统中的一个历史新闻批次文件。")
        export_desc.setWordWrap(True)
        layout.addWidget(export_desc)

        # 使用辅助函数配置历史文件下拉选择框
        self.export_combo = QComboBox()
        setup_combobox(self.export_combo) # 调用辅助函数
        layout.addWidget(self.export_combo)

        # --- 导出和删除按钮行 ---
        export_button_layout = QHBoxLayout()
        export_button_layout.setContentsMargins(0, 8, 0, 0) # 增加上边距
        export_button_layout.setSpacing(10)

        # 统一按钮样式
        button_style = """
            QPushButton {
                background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;
                padding: 6px 14px; color: #495057; font-size: 9pt;
            }
            QPushButton:hover { background-color: #e9ecef; border-color: #ced4da; }
            QPushButton:pressed { background-color: #dee2e6; }
            QPushButton:disabled { background-color: #f8f9fa; color: #adb5bd; border-color: #e9ecef; }
        """
        delete_button_style = button_style + """
            QPushButton { color: #dc3545; } /* 删除按钮红色文字 */
            QPushButton:hover { background-color: #f8d7da; border-color: #f5c6cb; } /* 悬停淡红色 */
            QPushButton:pressed { background-color: #f1b0b7; }
        """

        refresh_export_button = QPushButton("刷新列表")
        refresh_export_button.setStyleSheet(button_style)
        refresh_export_button.setToolTip("刷新可选的历史批次文件列表")
        refresh_export_button.clicked.connect(self._refresh_export_combo)
        export_button_layout.addWidget(refresh_export_button)

        export_json_button = QPushButton("导出为 JSON")
        export_json_button.setStyleSheet(button_style)
        export_json_button.setToolTip("将选中的历史批次导出为 JSON 文件")
        export_json_button.clicked.connect(self._export_selected_file) # Reuse existing JSON export logic
        export_button_layout.addWidget(export_json_button)

        export_csv_button = QPushButton("导出为 CSV") # NEW CSV Export
        export_csv_button.setStyleSheet(button_style)
        export_csv_button.setToolTip("将选中的历史批次导出为 CSV 文件")
        export_csv_button.clicked.connect(self._export_selected_to_csv) # Connect to new slot
        export_button_layout.addWidget(export_csv_button)

        export_button_layout.addStretch() # 将删除按钮推到右侧

        delete_selected_button = QPushButton("删除选中") # NEW Delete Selected
        delete_selected_button.setStyleSheet(delete_button_style)
        delete_selected_button.setToolTip("删除选中的历史批次文件")
        delete_selected_button.clicked.connect(self._delete_selected_batch) # Connect to new slot
        export_button_layout.addWidget(delete_selected_button)

        delete_all_button = QPushButton("删除全部") # NEW Delete All
        delete_all_button.setStyleSheet(delete_button_style)
        delete_all_button.setToolTip("删除所有历史批次文件（不可恢复）")
        delete_all_button.clicked.connect(self._delete_all_batches) # Connect to new slot
        export_button_layout.addWidget(delete_all_button)

        layout.addLayout(export_button_layout) # 添加按钮行到主布局

        layout.addStretch() # 将内容推到顶部

        # # 添加关闭按钮 (标准对话框按钮) # REMOVED
        # button_box = QPushButton("关闭") # REMOVED
        # button_box.clicked.connect(self.accept) # 点击关闭按钮接受对话框 # REMOVED
        # button_box.setStyleSheet("margin-top: 15px;") # REMOVED
        # layout.addWidget(button_box, 0, Qt.AlignRight) # 按钮靠右 # REMOVED

    # --- 以下方法从 HistoryPanel 移动过来 ---

    def _refresh_export_combo(self):
        """刷新导出文件下拉框"""
        self.logger.debug("_refresh_export_combo 方法被调用")
        if not hasattr(self, 'export_combo'):
            self.logger.warning("尝试刷新不存在的 export_combo")
            return

        # --- 添加日志：检查 self.news_dir 是否有效 ---
        if not hasattr(self, 'news_dir') or not self.news_dir:
            self.logger.error("_refresh_export_combo: self.news_dir 未定义或为空！")
            self.export_combo.clear()
            self.export_combo.addItem("错误：新闻目录未设置")
            return
        self.logger.info(f"_refresh_export_combo: 开始扫描目录: {self.news_dir}")
        # --- 日志结束 ---

        self.export_combo.clear()

        try:
            # self.logger.debug(f"扫描目录: {self.news_dir}") # 已在上面记录
            if not os.path.exists(self.news_dir):
                self.logger.warning(f"导出目录不存在: {self.news_dir}")
                self.export_combo.addItem(f"错误：目录不存在 {os.path.basename(self.news_dir)}") # 在下拉框提示错误
                return
            if not os.path.isdir(self.news_dir):
                 self.logger.error(f"导出路径不是一个目录: {self.news_dir}")
                 self.export_combo.addItem(f"错误：路径不是目录")
                 return

            # --- 添加日志：列出目录内容（如果文件不多） ---
            try:
                 all_entries = os.listdir(self.news_dir)
                 self.logger.debug(f"目录 '{self.news_dir}' 中的所有条目 ({len(all_entries)}): {all_entries[:20]}") # 最多显示前20个
            except Exception as list_err:
                 self.logger.error(f"无法列出目录 '{self.news_dir}' 的内容: {list_err}")
                 self.export_combo.addItem("错误：无法读取目录")
                 return
            # --- 日志结束 ---

            files = [f for f in all_entries if f.endswith('.json') and os.path.isfile(os.path.join(self.news_dir, f)) and '.corrupted_' not in f]
            self.logger.info(f"在 '{self.news_dir}' 中找到 {len(files)} 个符合条件的 .json 文件") # 改为 info 级别
            if not files:
                 self.logger.info("未找到任何历史批次文件。")
                 self.export_combo.addItem("没有找到历史批次文件") # 在下拉框提示
                 # 保持下拉框禁用或根据情况处理

            files.sort(reverse=True) # 按名称（通常是时间戳）降序排列

            for filename in files:
                self.logger.debug(f"处理文件: {filename}")
                display_text = filename # Default display text is the filename
                match = None  # <--- 初始化 match 为 None

                try:
                    if filename == "latest_news.json":
                        display_text = "最新新闻 (latest_news.json)"
                        # 在此分支中，match 保持为 None，后续的 if match 不会执行，符合预期
                    else:
                    # 尝试解析文件名中的日期时间戳
                    # 匹配 news_YYYYMMDD_HHMMSS.json 或 imported_*_YYYYMMDD_HHMMSS.json
                        match = re.match(r"(?:news_|imported_.*?_)(\d{8}_\d{6})\.json", filename)
                    
                    if match: # 现在即使 filename 是 latest_news.json，match 也是 None，不会报错，条件为假
                        date_str = match.group(1)
                        date_time = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        display_text = date_time.strftime('%Y-%m-%d %H:%M:%S') # Only show formatted timestamp
                    else:
                        # 如果不匹配标准格式，display_text 保持为原始 filename
                        self.logger.warning(f"文件名 \''{filename}\'' 不符合标准日期格式，直接显示文件名。")

                    self.export_combo.addItem(display_text, filename) # UserData 存储原始文件名
                    self.logger.debug(f"添加项目到 export_combo: '{display_text}' (Data: '{filename}')")
                except ValueError as date_parse_err:
                    self.logger.warning(f"解析文件名 '{filename}' 中的日期时出错 (ValueError): {date_parse_err}，直接显示文件名。")
                    self.export_combo.addItem(filename, filename) # Fallback to filename
                except Exception as item_err:
                     self.logger.error(f"处理文件 '{filename}' 并添加到下拉框时发生未知错误: {item_err}", exc_info=True)
                     # 可以选择跳过这个文件或添加一个错误项
                     # self.export_combo.addItem(f"错误: {filename}", filename)

            item_count = self.export_combo.count()
            self.logger.info(f"export_combo 刷新完成，共添加 {item_count} 个项目")
            # 根据是否有项目启用/禁用相关按钮
            can_export_or_delete = item_count > 0 and "错误：" not in self.export_combo.itemText(0) # 检查是否有有效项目
            # 需要找到导出和删除按钮并设置它们的 enabled 状态
            export_json_button = self.findChild(QPushButton, "exportJsonButton") # 假设按钮有 objectName
            export_csv_button = self.findChild(QPushButton, "exportCsvButton")
            delete_selected_button = self.findChild(QPushButton, "deleteSelectedButton")
            delete_all_button = self.findChild(QPushButton, "deleteAllButton")

            if export_json_button: export_json_button.setEnabled(can_export_or_delete)
            if export_csv_button: export_csv_button.setEnabled(can_export_or_delete)
            if delete_selected_button: delete_selected_button.setEnabled(can_export_or_delete)
            # 删除全部按钮应该总是可用，除非目录本身有问题？或者也根据是否有文件？(暂时保持总是可用)
            if delete_all_button: delete_all_button.setEnabled(item_count > 0) # 只有在有文件时才允许删除全部

        except Exception as e:
            self.logger.error(f"加载或处理导出文件列表时发生严重错误: {e}", exc_info=True)
            self.export_combo.clear()
            self.export_combo.addItem("错误：加载列表失败")

    def _import_news_file(self):
        """导入外部新闻文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入新闻文件", "", "JSON Files (*.json)"
        )
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                news_items = json.load(f)
            if not isinstance(news_items, list):
                QMessageBox.warning(self, "格式错误", "文件格式不正确，应为新闻条目列表")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"news_{timestamp}.json"
            new_path = os.path.join(self.news_dir, new_filename)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, ensure_ascii=False, indent=2)

            self._refresh_export_combo() # 导入成功后刷新下拉列表

            QMessageBox.information(
                self, "导入成功",
                f"成功导入 {len(news_items)} 条新闻\n保存为历史批次 {new_filename}"
            )
            self.logger.info(f"已导入 {len(news_items)} 条新闻到 {new_filename}")

        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入新闻文件失败: {str(e)}")
            self.logger.error(f"导入新闻文件失败: {str(e)}")

    def _export_selected_file(self):
        """导出当前选中的文件"""
        if not hasattr(self, 'export_combo') or self.export_combo.count() == 0:
            QMessageBox.warning(self, "提示", "没有可导出的文件")
            return

        selected_index = self.export_combo.currentIndex()
        if selected_index < 0:
            QMessageBox.warning(self, "提示", "请选择要导出的文件")
            return

        filename = self.export_combo.itemData(selected_index)
        file_path = os.path.join(self.news_dir, filename)

        if not os.path.exists(file_path):
            QMessageBox.critical(self, "错误", f"源文件不存在: {filename}")
            self.logger.error(f"尝试导出不存在的文件: {file_path}")
            return

        export_path, _ = QFileDialog.getSaveFileName(
            self, "导出新闻批次", filename, "JSON Files (*.json)"
        )
        if not export_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as src_file:
                news_items = json.load(src_file) # 读取以获取数量

            with open(file_path, 'rb') as src_file, open(export_path, 'wb') as dst_file:
                 dst_file.write(src_file.read())

            QMessageBox.information(
                self, "导出成功",
                f"成功导出包含 {len(news_items)} 条新闻的批次文件到:\n{export_path}"
            )
            self.logger.info(f"已将历史批次 {filename} ({len(news_items)} 条新闻) 导出到 {export_path}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出新闻失败: {str(e)}")
            self.logger.error(f"导出新闻失败: {str(e)}")

    def _export_selected_to_csv(self):
        """将选中的历史批次导出为 CSV 文件"""
        if not hasattr(self, 'export_combo') or self.export_combo.count() == 0:
            QMessageBox.warning(self, "提示", "没有可导出的文件")
            return

        selected_index = self.export_combo.currentIndex()
        if selected_index < 0:
            QMessageBox.warning(self, "提示", "请选择要导出的文件")
            return

        filename_json = self.export_combo.itemData(selected_index)
        file_path_json = os.path.join(self.news_dir, filename_json)

        if not os.path.exists(file_path_json):
            QMessageBox.critical(self, "错误", f"源 JSON 文件不存在: {filename_json}")
            self.logger.error(f"尝试导出 CSV 时源 JSON 文件不存在: {file_path_json}")
            return

        # 建议的 CSV 文件名
        filename_csv = os.path.splitext(filename_json)[0] + ".csv"

        export_path_csv, _ = QFileDialog.getSaveFileName(
            self, "导出为 CSV", filename_csv, "CSV Files (*.csv)"
        )
        if not export_path_csv: return

        try:
            import csv
            with open(file_path_json, 'r', encoding='utf-8') as f_json:
                news_items = json.load(f_json)

            if not news_items:
                QMessageBox.information(self, "提示", "选中的 JSON 文件为空，无法导出 CSV。")
                return

            # 定义 CSV 表头 (根据 NewsArticle 模型或 JSON 结构)
            # 注意：这里假设了 JSON 中字典的键是固定的，实际可能需要更健壮的处理
            fieldnames = ['title', 'link', 'source_name', 'publish_time', 'category', 'summary', 'content']
            # 确保所有可能的键都在里面，即使某些条目可能缺少某些键
            all_keys = set()
            for item in news_items:
                all_keys.update(item.keys())
            # 可以根据需要调整最终的 fieldnames 顺序或包含哪些字段
            fieldnames = sorted(list(all_keys)) # 或者使用预定义的 fieldnames

            with open(export_path_csv, 'w', newline='', encoding='utf-8-sig') as f_csv: # utf-8-sig 确保 Excel 正确识别 BOM
                writer = csv.DictWriter(f_csv, fieldnames=fieldnames, extrasaction='ignore') # extrasaction='ignore' 忽略 news_items 中多余的键
                writer.writeheader()
                writer.writerows(news_items)

            QMessageBox.information(
                self, "导出成功",
                f"成功将 {len(news_items)} 条新闻导出为 CSV 文件到:\n{export_path_csv}"
            )
            self.logger.info(f"已将历史批次 {filename_json} ({len(news_items)} 条新闻) 导出为 CSV 到 {export_path_csv}")

        except ImportError:
             QMessageBox.critical(self, "错误", "导出 CSV 需要 'csv' 模块，未能找到。")
             self.logger.error("导出 CSV 失败：缺少 csv 模块")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出 CSV 文件失败: {str(e)}")
            self.logger.error(f"导出 CSV 文件失败: {str(e)}", exc_info=True)

    def _delete_selected_batch(self):
        """删除选中的历史批次文件"""
        if not hasattr(self, 'export_combo') or self.export_combo.count() == 0:
            QMessageBox.warning(self, "提示", "没有可删除的文件")
            return

        selected_index = self.export_combo.currentIndex()
        if selected_index < 0:
            QMessageBox.warning(self, "提示", "请选择要删除的文件")
            return

        filename = self.export_combo.itemData(selected_index)
        display_name = self.export_combo.currentText()
        file_path = os.path.join(self.news_dir, filename)

        reply = QMessageBox.question(
            self, '确认删除',
            f"确定要删除历史批次文件吗？\n\n{display_name}\n\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"已删除历史批次文件: {file_path}")
                QMessageBox.information(self, "删除成功", f"已删除文件:\n{filename}")
                self._refresh_export_combo() # 删除后刷新列表
            else:
                QMessageBox.warning(self, "错误", f"文件不存在，可能已被删除: {filename}")
                self.logger.warning(f"尝试删除不存在的文件: {file_path}")
                self._refresh_export_combo() # 刷新列表以反映变化

        except Exception as e:
            QMessageBox.critical(self, "删除失败", f"删除文件失败: {str(e)}")
            self.logger.error(f"删除文件失败: {str(e)}", exc_info=True)

    def _delete_all_batches(self):
        """删除所有历史批次文件"""
        reply = QMessageBox.question(
            self, '确认删除全部',
            "确定要删除所有历史新闻批次文件吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        deleted_count = 0
        errors = []
        try:
            if not os.path.exists(self.news_dir):
                QMessageBox.information(self, "提示", "新闻目录不存在，无需删除。")
                return

            for filename in os.listdir(self.news_dir):
                if filename.endswith('.json') and filename.startswith('news_'): # 只删除符合命名规范的 json 文件
                    file_path = os.path.join(self.news_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.debug(f"已删除文件: {file_path}")
                    except Exception as e:
                        errors.append(filename)
                        self.logger.error(f"删除文件 {filename} 失败: {e}")

            self._refresh_export_combo() # 删除后刷新列表

            if errors:
                QMessageBox.warning(self, "部分删除失败", f"成功删除 {deleted_count} 个文件。\n以下文件删除失败:\n" + "\n".join(errors))
            else:
                QMessageBox.information(self, "删除成功", f"已成功删除 {deleted_count} 个历史批次文件。")
            self.logger.info(f"执行删除全部批次操作，删除了 {deleted_count} 个文件，失败 {len(errors)} 个。")

        except Exception as e:
            QMessageBox.critical(self, "删除失败", f"删除全部批次文件时发生错误: {str(e)}")
            self.logger.error(f"删除全部批次文件时发生错误: {str(e)}", exc_info=True)

    def closeEvent(self, event):
        """Override close event to ensure cleanup for non-modal dialog."""
        self.logger.debug("ImportExportDialog: closeEvent triggered. Accepting event.")
        # 确保事件被接受
        event.accept() # 明确接受关闭事件
        # DO NOT call deleteLater here. Let the connected finished signal handle it.
        # self.closed_and_deleted.emit() # REMOVED signal emit
        # self.deleteLater() # REMOVED - Handled by MainWindow._on_import_export_closed


