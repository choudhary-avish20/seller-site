# Test Images

Drop your test product images here (.jpg, .jpeg, .png, .webp, .gif, .avif).

- Files here are listed via GET /api/v1/uploads/test-images
- Retrieve via GET /api/v1/uploads/test-images/{filename}
- Seller panel "Add Product" shows these as quick-add buttons.

For real uploads, files go to `backend/uploads/products/` via POST /api/v1/uploads/image (seller auth, 10MB limit).

Backend serves uploads at http://localhost:8000/uploads/products/{file} and http://localhost:8000/api/v1/uploads/test-images/{file}
