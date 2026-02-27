import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QListWidget, QListWidgetItem, QStackedWidget, QScrollArea, QCheckBox,
                             QSplashScreen)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QCoreApplication, QTimer
from ui.home_view import HomeView
from ui.browser_view import BrowserView
from ui.reader_view import ReaderView
from ui.settings_view import SettingsView
from ui.bookmarks_view import BookmarksView
from ui.projects_view import ProjectsView
from ui.extensions_view import ExtensionsSettingsView
from ui.downloads_view import DownloadsView
from ui.about_dialog import AboutDialog
from database import BookmarkManager, DatabaseManager, ExtensionManager, DownloadManager
from research_managers import ProjectManager, TagManager, AnnotationManager
from extensions import ExtensionManager as ExtensionManagerCore
from sample_extensions import DOAJExtension, OpenLibraryExtension, ArxivExtension, WikipediaExtension, CrossrefExtension
from constants import EXTENSIONS_DIR


class KnowledgedockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Knowledgedock")
        self.setWindowIcon(QIcon(os.path.join("assets", "cover.png")))
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(self.get_modern_stylesheet())
        
        # Initialize database managers
        self.db_manager = DatabaseManager()
        self.bookmark_manager = BookmarkManager(self.db_manager.db_path)
        self.extension_db_manager = ExtensionManager(self.db_manager.db_path)
        self.download_manager = DownloadManager(self.db_manager.db_path)
        
        # Initialize Research Dashboard managers
        self.project_manager = ProjectManager(self.db_manager.db_path)
        self.tag_manager = TagManager(self.db_manager.db_path)
        self.annotation_manager = AnnotationManager(self.db_manager.db_path)
        
        # Initialize extension manager and register sample extensions
        self.extension_manager = ExtensionManagerCore(str(EXTENSIONS_DIR))
        self.setup_extensions()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = self.create_sidebar()
        layout.addWidget(self.sidebar)
        
        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.home_view = HomeView(self.extension_manager, self.bookmark_manager)
        self.reader_view = ReaderView(self.annotation_manager)
        self.browser_view = BrowserView(self.bookmark_manager, self.extension_manager, self.reader_view)
        self.bookmarks_view = BookmarksView(self.bookmark_manager)
        self.projects_view = ProjectsView(self.project_manager)
        self.extensions_view = ExtensionsSettingsView(self.extension_db_manager, self.db_manager, self.extension_manager)
        self.settings_view = SettingsView()
        self.downloads_view = DownloadsView(self.download_manager)
        
        self.stacked_widget.addWidget(self.home_view)
        self.stacked_widget.addWidget(self.browser_view)
        self.stacked_widget.addWidget(self.bookmarks_view)
        self.stacked_widget.addWidget(self.projects_view)
        self.stacked_widget.addWidget(self.extensions_view)
        self.stacked_widget.addWidget(self.reader_view)
        self.stacked_widget.addWidget(self.settings_view)
        self.stacked_widget.addWidget(self.downloads_view)
        
        # Connect home view signals
        self.home_view.browse_requested.connect(self.show_browser)
        self.home_view.bookmarks_requested.connect(self.show_bookmarks)
        self.home_view.projects_requested.connect(self.show_projects)
        self.home_view.extensions_requested.connect(self.show_extensions)
        self.home_view.settings_requested.connect(self.show_settings)
        
        # Connect projects view signals
        self.projects_view.resource_clicked.connect(self.read_from_project)
        
        # Connect reader view signals
        self.reader_view.back_requested.connect(self.show_browser)
        self.reader_view.bookmark_requested.connect(self.handle_reader_bookmark)
        self.reader_view.add_to_project_requested.connect(self.handle_add_to_project)

        # Connect settings signals to apply changes
        self.settings_view.settings_applied.connect(self.apply_settings)
        
        layout.addWidget(self.stacked_widget, 1)
        
        # Show home view by default
        self.show_home()
    
    def setup_extensions(self):
        """Setup and register default extensions"""
        try:
            # Register sample extensions
            self.extension_manager.register_extension("doaj", DOAJExtension())
            self.extension_manager.register_extension("openlibrary", OpenLibraryExtension())
            self.extension_manager.register_extension("arxiv", ArxivExtension())
            self.extension_manager.register_extension("wikipedia", WikipediaExtension())
            self.extension_manager.register_extension("crossref", CrossrefExtension())
            
            # Register in database
            self.extension_db_manager.register_extension("DOAJ", "2.0.0", "Knowledgedock", "Browse open access journals")
            self.extension_db_manager.register_extension("Open Library", "1.0.0", "Knowledgedock", "Browse Open Library books")
            self.extension_db_manager.register_extension("arXiv", "1.0.0", "Knowledgedock", "Browse research papers")
            self.extension_db_manager.register_extension("Wikipedia", "1.0.0", "Knowledgedock", "Browse Wikipedia articles")
            self.extension_db_manager.register_extension("Crossref", "1.0.0", "Knowledgedock", "Access academic research metadata")
        except Exception as e:
            print(f"Error setting up extensions: {e}")
    
    
    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
                border-right: 1px solid rgba(59, 130, 246, 0.2);
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Title with gradient
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 25, 20, 25)
        title_layout.setSpacing(5)
        
        title = QLabel("KNOWLEDGEDOCK")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #3b82f6;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Learn & Explore")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic;")
        title_layout.addWidget(subtitle)
        
        title_container.setStyleSheet("""
            background: linear-gradient(180deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
            border-bottom: 1px solid rgba(59, 130, 246, 0.1);
        """)
        layout.addWidget(title_container)
        
        # Spacer
        spacer = QWidget()
        spacer.setFixedHeight(20)
        layout.addWidget(spacer)
        
        # Navigation buttons with icons
        nav_buttons = [
            ("🏠", "Home", self.show_home),
            ("📚", "Browse", self.show_browser),
            ("📁", "Projects", self.show_projects),
            ("❤️", "Bookmarks", self.show_bookmarks),
            ("⚡", "Extensions", self.show_extensions),
            ("📖", "Reader", self.show_reader),
            ("📥", "Downloads", self.show_downloads),
            ("⚙️", "Settings", self.show_settings),
            ("ℹ️", "About", self.show_about),
        ]
        
        for icon, text, callback in nav_buttons:
            btn = QPushButton(f"{icon}  {text}")
            btn.setMinimumHeight(48)
            btn.setFont(QFont("Segoe UI", 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #cbd5e1;
                    border: none;
                    padding: 12px 20px;
                    text-align: left;
                    font-weight: 500;
                    margin: 4px 12px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(59, 130, 246, 0.15);
                    color: #3b82f6;
                    padding-left: 24px;
                }
                QPushButton:pressed {
                    background-color: rgba(59, 130, 246, 0.25);
                }
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        # Spacer at bottom
        layout.addStretch()
        
        # Footer with version
        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(20, 15, 20, 15)
        footer_layout.setSpacing(0)
        
        version_label = QLabel("v2.1 Blue")
        version_label.setFont(QFont("Segoe UI", 8))
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            color: #64748b;
            padding: 8px;
            border-top: 1px solid rgba(59, 130, 246, 0.1);
        """)
        footer_layout.addWidget(version_label)
        layout.addWidget(footer)
        
        return sidebar
    
    def show_home(self):
        # Refresh home view with latest data
        if hasattr(self.home_view, 'refresh_stats'):
            self.home_view.refresh_stats()
        self.stacked_widget.setCurrentWidget(self.home_view)
    
    def show_browser(self):
        self.stacked_widget.setCurrentWidget(self.browser_view)
    
    def show_bookmarks(self):
        self.bookmarks_view.refresh()
        self.stacked_widget.setCurrentWidget(self.bookmarks_view)
        
    def show_projects(self):
        self.stacked_widget.setCurrentWidget(self.projects_view)
        self.projects_view.load_projects()
        
    def read_from_project(self, url, title):
        """Open a resource from a project in the reader"""
        resource = {
            'url': url,
            'title': title
        }
        self.reader_view.load_resource(resource, title, "Project Collection")
        self.show_reader()
    
    def show_extensions(self):
        self.stacked_widget.setCurrentWidget(self.extensions_view)

    def handle_reader_bookmark(self, title, url, extension_name):
        """Handle bookmark request emitted from the reader view"""
        if url and url != '#':
            self.bookmark_manager.add_bookmark(
                title=title,
                url=url,
                source=extension_name,
                resource_type="Reader"
            )
            # Keep bookmarks view in sync
            if hasattr(self.bookmarks_view, 'refresh'):
                self.bookmarks_view.refresh()

    def handle_add_to_project(self, title, url, extension_name):
        """Handle adding current reader resource to a project"""
        # Quick dialog to pick a project
        projects = self.project_manager.get_all_projects()
        if not projects:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Projects", "Please create a project in the Projects view first.")
            return
            
        project_names = [p[1] for p in projects] # [1] is name
        
        from PyQt5.QtWidgets import QInputDialog
        project_name, ok = QInputDialog.getItem(self, "Select Project", 
                                                "Add to Project:", project_names, 0, False)
        
        if ok and project_name:
            # Find ID for the selected name
            project_id = next((p[0] for p in projects if p[1] == project_name), None)
            if project_id:
                if self.project_manager.add_resource_to_project(project_id, url, title):
                    # Refresh the projects view so it shows up immediately
                    if hasattr(self.projects_view, 'load_projects'):
                        self.projects_view.load_projects()
                        
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(self, "Success", f"Added '{title[:30]}...' to '{project_name}'")
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Error", "Failed to add to project.")


    def show_reader(self):
        self.stacked_widget.setCurrentWidget(self.reader_view)
    
    def show_downloads(self):
        self.downloads_view.refresh_downloads()
        self.stacked_widget.setCurrentWidget(self.downloads_view)
    
    def show_settings(self):
        self.stacked_widget.setCurrentWidget(self.settings_view)
    
    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def apply_settings(self, settings):
        """Apply settings to the application"""
        try:
            # Apply theme
            theme = settings.get('theme', 'Dark')
            if theme == 'Dark':
                self.setStyleSheet(self.get_modern_stylesheet())
            elif theme == 'Light':
                # Could implement light theme here
                self.setStyleSheet(self.get_modern_stylesheet())
            
            # Apply compact view if enabled
            if settings.get('compact_view', False):
                # Could adjust font sizes, padding, etc.
                pass
            
            # Apply viewer zoom
            if hasattr(self, 'reader_view'):
                zoom = settings.get('viewer_zoom', 100)
                self.reader_view.zoom_level = zoom
                self.reader_view.web_view.setZoomFactor(zoom / 100.0)
                if hasattr(self.reader_view, 'zoom_label'):
                    self.reader_view.zoom_label.setText(f"{zoom}%")
            
        except Exception as e:
            print(f"Error applying settings: {e}")
    
    @staticmethod
    def get_modern_stylesheet():
        return """
            QWidget:focus { outline: none; }
            * { outline: none; }
            
            /* Main Window */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1b4b, stop:1 #083344);
            }
            
            /* Widget Base */
            QWidget {
                background: transparent;
                color: #f1f5f9;
            }
            
            /* LineEdit - Modern Search/Input */
            QLineEdit {
                background-color: rgba(30, 41, 59, 0.6);
                color: #f1f5f9;
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                padding: 10px 15px;
                font: 11pt "Segoe UI";
                selection-background-color: rgba(59, 130, 246, 0.4);
            }
            
            QLineEdit:hover {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(59, 130, 246, 0.6);
            }
            
            QLineEdit:focus {
                background-color: rgba(30, 41, 59, 1.0);
                border: 2px solid #3b82f6;
                padding: 10px 14px;
            }
            
            /* Buttons - Modern Style */
            QPushButton {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font: 11pt "Segoe UI";
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            
            QPushButton:hover {
                background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            }
            
            QPushButton:pressed {
                background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            }
            
            QPushButton:disabled {
                background: rgba(59, 130, 246, 0.3);
                color: rgba(241, 245, 249, 0.5);
            }
            
            /* List Widget */
            QListWidget {
                background-color: rgba(30, 41, 59, 0.5);
                color: #f1f5f9;
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 8px;
                outline: none;
            }
            
            QListWidget::item {
                padding: 10px;
                margin: 2px 4px;
                border-radius: 6px;
            }
            
            QListWidget::item:hover {
                background-color: rgba(59, 130, 246, 0.1);
                color: #60a5fa;
            }
            
            QListWidget::item:selected {
                background: linear-gradient(90deg, rgba(59, 130, 246, 0.2) 0%, transparent 100%);
                border-left: 3px solid #3b82f6;
                color: #3b82f6;
                font-weight: bold;
            }
            
            /* Scrollbars - Modern */
            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background: linear-gradient(180deg, rgba(59, 130, 246, 0.4), rgba(59, 130, 246, 0.2));
                border-radius: 5px;
                min-height: 20px;
                margin: 2px 0px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: linear-gradient(180deg, rgba(59, 130, 246, 0.6), rgba(59, 130, 246, 0.4));
            }
            
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                border: none;
                background: none;
            }
            
            QScrollBar:horizontal {
                background-color: transparent;
                height: 10px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background: linear-gradient(90deg, rgba(59, 130, 246, 0.4), rgba(59, 130, 246, 0.2));
                border-radius: 5px;
                min-width: 20px;
                margin: 0px 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: linear-gradient(90deg, rgba(59, 130, 246, 0.6), rgba(59, 130, 246, 0.4));
            }
            
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
                border: none;
                background: none;
            }
            
            /* Label */
            QLabel {
                color: #cbd5e1;
            }
            
            /* Frame - for sections */
            QFrame {
                background-color: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(59, 130, 246, 0.1);
                border-radius: 10px;
            }
            
            /* ComboBox */
            QComboBox {
                background-color: rgba(30, 41, 59, 0.6);
                color: #f1f5f9;
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 28px;
            }
            
            QComboBox:hover {
                border: 1px solid rgba(59, 130, 246, 0.5);
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f1f5f9;
                selection-background-color: rgba(59, 130, 246, 0.3);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 6px;
            }
            
            /* SpinBox */
            QSpinBox, QDoubleSpinBox {
                background-color: rgba(30, 41, 59, 0.6);
                color: #f1f5f9;
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
            }
            
            /* CheckBox & RadioButton */
            QCheckBox, QRadioButton {
                color: #f1f5f9;
                spacing: 5px;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid rgba(59, 130, 246, 0.4);
                background-color: rgba(30, 41, 59, 0.6);
            }
            
            QCheckBox::indicator:hover, QRadioButton::indicator:hover {
                border: 1px solid rgba(59, 130, 246, 0.8);
            }
            
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                background-color: #3b82f6;
                border: 1px solid #3b82f6;
            }
        """


if __name__ == "__main__":
    # Disable GPU in the Chromium process inside QWebEngineView.
    # AA_UseSoftwareOpenGL conflicts with WebEngine and causes GPU-process crashes.
    # These env vars must be set BEFORE QApplication is created.
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing --no-sandbox"
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

    app = QApplication(sys.argv)
    
    # Define absolute path to assets
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cover_path = os.path.join(base_dir, "assets", "cover.png")

    # Set application-wide icon
    app_icon = QIcon(cover_path)
    app.setWindowIcon(app_icon)
    
    # Create and show splash screen
    splash_pix = QPixmap(cover_path)
    if not splash_pix.isNull():
        # Resize pixmap for splash if needed
        splash_pix = splash_pix.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        
        # Modern splash styling
        splash.show()
    else:
        # Fallback if image failed to load for some reason
        splash = QSplashScreen(Qt.WindowStaysOnTopHint)
        splash.showMessage("Loading Knowledgedock...", Qt.AlignCenter, Qt.white)
        splash.show()
    app.processEvents()
    
    # Load the main window
    window = KnowledgedockApp()
    
    # Simulate some loading time or wait for initialization
    QTimer.singleShot(2500, lambda: (window.show(), splash.finish(window)))
    
    sys.exit(app.exec_())
