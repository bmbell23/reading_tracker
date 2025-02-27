import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.book import Book
from src.models.inventory import Inventory

class TestInventoryOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create test database"""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up fresh test data before each test"""
        self.session = self.Session()
        
        # Create test book
        self.test_book = Book(
            title="Inventory Test Book",
            author="Test Author"
        )
        self.session.add(self.test_book)
        self.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        self.session.query(Inventory).delete()
        self.session.query(Book).delete()
        self.session.commit()
        self.session.close()

    def test_inventory_creation(self):
        """Test creating new inventory entry"""
        inventory = Inventory(
            book_id=self.test_book.id,
            owned_physical=True,
            owned_kindle=False,
            owned_audio=False,
            date_purchased=date.today(),
            location="Main Shelf",
            read_status="Unread",
            read_count=0,
            isbn_10="1234567890",
            isbn_13="1234567890123"
        )

        self.session.add(inventory)
        self.session.commit()

        # Verify inventory entry
        saved_inventory = (self.session.query(Inventory)
                          .filter_by(book_id=self.test_book.id)
                          .first())

        self.assertTrue(saved_inventory.owned_physical)
        self.assertFalse(saved_inventory.owned_kindle)
        self.assertEqual(saved_inventory.location, "Main Shelf")
        self.assertEqual(saved_inventory.isbn_10, "1234567890")
        self.assertEqual(saved_inventory.isbn_13, "1234567890123")
        self.assertTrue(saved_inventory.owned_overall)

    def test_inventory_update(self):
        """Test updating inventory information"""
        # Create initial inventory
        inventory = Inventory(
            book_id=self.test_book.id,
            owned_physical=True,
            read_status="Unread",
            read_count=0
        )
        self.session.add(inventory)
        self.session.commit()

        # Update inventory
        inventory.read_status = "Reading"
        inventory.read_count = 1
        inventory.owned_kindle = True
        self.session.commit()

        # Verify updates
        updated_inventory = (self.session.query(Inventory)
                           .filter_by(book_id=self.test_book.id)
                           .first())

        self.assertEqual(updated_inventory.read_status, "Reading")
        self.assertEqual(updated_inventory.read_count, 1)
        self.assertTrue(updated_inventory.owned_kindle)
        self.assertTrue(updated_inventory.owned_overall)

    def test_inventory_formats(self):
        """Test managing multiple format ownership"""
        # Create new inventory entry
        inventory = Inventory(
            book_id=self.test_book.id,
            owned_physical=True,
            owned_kindle=True,
            owned_audio=False
        )
        self.session.add(inventory)
        self.session.commit()

        # Test format queries
        physical_books = (self.session.query(Inventory)
                         .filter_by(owned_physical=True)
                         .all())
        kindle_books = (self.session.query(Inventory)
                       .filter_by(owned_kindle=True)
                       .all())
        audio_books = (self.session.query(Inventory)
                      .filter_by(owned_audio=True)
                      .all())

        self.assertEqual(len(physical_books), 1)
        self.assertEqual(len(kindle_books), 1)
        self.assertEqual(len(audio_books), 0)

    def test_inventory_relationship(self):
        """Test the relationship between Inventory and Book"""
        inventory = Inventory(
            book_id=self.test_book.id,
            owned_physical=True
        )
        self.session.add(inventory)
        self.session.commit()
        
        # Refresh from database to ensure we have current data
        self.session.refresh(inventory)
        self.session.refresh(self.test_book)
        
        self.assertEqual(inventory.book.title, "Inventory Test Book")

if __name__ == '__main__':
    unittest.main()
