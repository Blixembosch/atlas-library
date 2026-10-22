"""Tests for services/isbn_service.py."""

import unittest
from unittest.mock import patch, MagicMock

import services.isbn_service
from services.isbn_service import fetch_book_by_isbn


class TestISBNService(unittest.TestCase):
    def test_empty_isbn(self):
        self.assertIsNone(fetch_book_by_isbn(""))
        self.assertIsNone(fetch_book_by_isbn("---"))

    def test_valid_isbn_mocked(self):
        mock_req = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "De Kleine Prins",
            "number_of_pages": 96,
            "publishers": ["De Vuurvlinder"],
            "covers": [12345],
        }
        mock_req.get.return_value = mock_resp

        with patch.object(services.isbn_service, "requests", mock_req):
            res = fetch_book_by_isbn("9789025812345")
            self.assertIsNotNone(res)
            self.assertEqual(res["title"], "De Kleine Prins")
            self.assertEqual(res["pages"], 96)
            self.assertIn("12345-L.jpg", res["cover_url"])


if __name__ == "__main__":
    unittest.main()
