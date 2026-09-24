import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Testimonial


def _jpeg(size=(2400, 1200)):
    buf = io.BytesIO()
    Image.new("RGB", size, "orange").save(buf, "JPEG")
    return SimpleUploadedFile("trip.jpg", buf.getvalue(), content_type="image/jpeg")


REVIEW = {
    "fname": "Test",
    "lname": "Guest",
    "email": "",
    "rating": "4",
    "fdate": "2026-09-01",
    "tdate": "2026-09-05",
    "content": "Wonderful desert camp and a brilliant guide.",
}


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SubmitYourReviewTests(TestCase):
    def test_form_renders_with_and_without_trailing_slash(self):
        self.assertEqual(self.client.get("/submit-your-review/").status_code, 200)
        response = self.client.get("/submit-your-review")
        self.assertRedirects(response, "/submit-your-review/", status_code=301)

    def test_submission_is_published_on_testimonials_and_home(self):
        response = self.client.post(reverse("submit_your_review"), REVIEW, follow=True)
        self.assertRedirects(response, reverse("testimonials"))
        self.assertContains(response, "Wonderful desert camp")
        self.assertContains(response, "Test Guest")
        self.assertContains(response, "01 Sep 2026 to 05 Sep 2026")
        self.assertContains(self.client.get("/"), "Wonderful desert camp")

    def test_uploaded_photo_is_stored_in_database_and_served(self):
        self.client.post(reverse("submit_your_review"), {**REVIEW, "image": _jpeg()})
        review = Testimonial.objects.get(name="Test Guest")
        self.assertFalse(review.image)
        self.assertEqual(review.photo_content_type, "image/jpeg")

        photo_url = reverse("testimonial_photo", args=[review.pk])
        self.assertContains(self.client.get(reverse("testimonials")), photo_url)

        response = self.client.get(photo_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        with Image.open(io.BytesIO(response.content)) as img:
            self.assertLessEqual(max(img.size), 1600)

    def test_unpublished_photo_is_hidden(self):
        self.client.post(reverse("submit_your_review"), {**REVIEW, "image": _jpeg()})
        review = Testimonial.objects.get(name="Test Guest")
        review.is_published = False
        review.save()
        response = self.client.get(reverse("testimonial_photo", args=[review.pk]))
        self.assertEqual(response.status_code, 404)

    def test_to_date_before_from_date_is_rejected(self):
        response = self.client.post(
            reverse("submit_your_review"), {**REVIEW, "tdate": "2026-08-01"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "To date must be on or after From date.")
        self.assertFalse(Testimonial.objects.filter(name="Test Guest").exists())

    def test_deploy_seed_keeps_guest_review_with_canonical_name(self):
        call_command("seed_marketing", verbosity=0)
        canonical = Testimonial.objects.filter(date_from__isnull=True).first()
        first, last = canonical.name.split(" ", 1)
        self.client.post(reverse("submit_your_review"), {**REVIEW, "fname": first, "lname": last})
        guest = Testimonial.objects.get(name=canonical.name, date_from__isnull=False)
        call_command("seed_marketing", "--if-empty", verbosity=0)
        guest.refresh_from_db()
        self.assertEqual(guest.quote, REVIEW["content"])
