from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, require_seller_or_admin
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryMove,
    CategoryResponse,
    CategoryTreeNode,
    CategoryPathResponse,
    slugify,
)

router = APIRouter(prefix="/categories", tags=["categories"])


def _ensure_slug_unique(db: Session, slug: str, exclude_id: Optional[UUID] = None) -> None:
    q = db.query(Category).filter(Category.slug == slug)
    if exclude_id:
        q = q.filter(Category.id != exclude_id)
    if q.first():
        raise HTTPException(status_code=400, detail=f"Slug '{slug}' already exists")


def _check_parent(db: Session, parent_id: Optional[UUID], self_id: Optional[UUID] = None) -> Optional[Category]:
    if parent_id is None:
        return None
    if self_id and parent_id == self_id:
        raise HTTPException(status_code=400, detail="Category cannot be its own parent")
    parent = db.query(Category).filter(Category.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent category not found")
    # prevent circular: walk up chain
    if self_id:
        current = parent
        visited = set()
        while current and current.parent_id:
            if current.parent_id == self_id:
                raise HTTPException(status_code=400, detail="Circular parent reference detected")
            if current.parent_id in visited:
                break
            visited.add(current.parent_id)
            current = db.query(Category).filter(Category.id == current.parent_id).first()
    return parent


def _build_tree(categories: List[Category]) -> List[CategoryTreeNode]:
    # build id -> node mapping
    id_to_node = {}
    for c in categories:
        id_to_node[str(c.id)] = CategoryTreeNode(
            id=c.id,
            name=c.name,
            slug=c.slug,
            parent_id=c.parent_id,
            is_active=c.is_active,
            sort_order=c.sort_order,
            created_at=c.created_at,
            updated_at=c.updated_at,
            children=[],
        )
    roots: List[CategoryTreeNode] = []
    for c in categories:
        node = id_to_node[str(c.id)]
        if c.parent_id and str(c.parent_id) in id_to_node:
            parent_node = id_to_node[str(c.parent_id)]
            parent_node.children.append(node)
        else:
            roots.append(node)
    # Top-level categories keep the admin's manual sort_order (arrows in the
    # dashboard); every subcategory level below that is always alphabetical —
    # it has no manual ordering control at all.
    roots.sort(key=lambda n: (n.sort_order, n.name.lower()))

    def sort_children_recursive(nodes: List[CategoryTreeNode]):
        for n in nodes:
            n.children.sort(key=lambda c: c.name.lower())
            sort_children_recursive(n.children)
    sort_children_recursive(roots)
    return roots


# ------------- Public: tree & list -------------
@router.get("/tree", response_model=List[CategoryTreeNode])
def get_category_tree(
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False, description="Admin can include inactive"),
    # we allow optional auth to decide, but public default false
):
    q = db.query(Category)
    if not include_inactive:
        q = q.filter(Category.is_active == True)  # noqa
    categories = q.order_by(Category.name).all()
    return _build_tree(categories)


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    parent_id: Optional[UUID] = Query(None),
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None),
):
    q = db.query(Category)
    if not include_inactive:
        q = q.filter(Category.is_active == True)  # noqa
    if parent_id is not None:
        q = q.filter(Category.parent_id == parent_id)
    if search:
        q = q.filter(Category.name.ilike(f"%{search}%"))
    # This flat listing is always alphabetical (it's used for searching/filtering,
    # and may mix categories from different levels). The admin's manual
    # top-level order only applies to the tree view (GET /categories/tree),
    # which is what the dashboard and storefront navigation actually render.
    q = q.order_by(Category.name)
    return q.all()


@router.get("/by-slug/{slug}", response_model=CategoryResponse)
def get_by_slug(slug: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.get("/by-path/{path:path}", response_model=CategoryPathResponse)
def get_by_path(path: str, db: Session = Depends(get_db)):
    """
    Fetch category by slash-separated path e.g. electronics/phones/smartphones
    Each segment is a slug. Verifies parent chain.
    """
    slugs = [s for s in path.strip("/").split("/") if s]
    if not slugs:
        raise HTTPException(status_code=404, detail="Empty path")
    ancestors: List[Category] = []
    current: Optional[Category] = None
    parent_id: Optional[UUID] = None
    for slug in slugs:
        q = db.query(Category).filter(Category.slug == slug)
        if parent_id is None:
            # top-level: parent_id is None
            q = q.filter(Category.parent_id.is_(None))
        else:
            q = q.filter(Category.parent_id == parent_id)
        cat = q.first()
        if not cat:
            raise HTTPException(status_code=404, detail=f"Path segment '{slug}' not found")
        if current:
            ancestors.append(current)
        current = cat
        parent_id = cat.id
    assert current is not None
    full_path = "/".join(slugs)
    return CategoryPathResponse(category=current, ancestors=ancestors, path=full_path)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: UUID, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


# ------------- Admin CRUD -------------
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    if not slug:
        slug = slugify(payload.name)
    _ensure_slug_unique(db, slug)
    _check_parent(db, payload.parent_id)

    # New top-level categories join the end of the manually-ordered list.
    # Subcategories don't use sort_order at all (always alphabetical), so it's
    # left at the column default there.
    sort_order = 0
    if payload.parent_id is None:
        current_max = db.query(Category.sort_order).filter(Category.parent_id.is_(None)).order_by(Category.sort_order.desc()).first()
        sort_order = (current_max[0] + 10) if current_max else 0

    cat = Category(
        name=payload.name.strip(),
        slug=slug,
        parent_id=payload.parent_id,
        is_active=payload.is_active,
        sort_order=sort_order,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.name is not None:
        cat.name = payload.name.strip()
    if payload.slug is not None:
        new_slug = payload.slug.strip() or slugify(cat.name)
        _ensure_slug_unique(db, new_slug, exclude_id=cat.id)
        cat.slug = new_slug
    elif payload.name is not None:
        # if name changed and slug not explicitly provided, keep existing slug (don't auto-rename) to avoid breaking URLs
        pass

    if payload.parent_id is not None:
        # allow explicit null to move to top-level; to support that, client must send null
        # But our schema treats omitted vs null ambiguous; we check if field was set
        # Pydantic: if payload.parent_id is provided as None explicitly, it will be None
        # To distinguish omitted vs set-to-None, we check __fields_set__
        pass

    # proper handling of parent_id including null
    if "parent_id" in payload.model_fields_set:
        _check_parent(db, payload.parent_id, self_id=cat.id)
        # Promoting a subcategory to top-level: it has no meaningful sort_order
        # yet, so append it at the end of the manually-ordered root list rather
        # than leaving it at the default 0 (which would jump it to the top).
        if payload.parent_id is None and cat.parent_id is not None:
            current_max = db.query(Category.sort_order).filter(Category.parent_id.is_(None)).order_by(Category.sort_order.desc()).first()
            cat.sort_order = (current_max[0] + 10) if current_max else 0
        cat.parent_id = payload.parent_id

    if payload.is_active is not None:
        cat.is_active = payload.is_active

    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/{category_id}/move", response_model=CategoryResponse)
def move_category(
    category_id: UUID,
    payload: CategoryMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    """Move a top-level category up or down one slot in the admin's manual
    order (swaps sort_order with whichever root sibling is on that side).
    Subcategories have no manual order — they're always alphabetical — so
    this is refused for anything that isn't itself a root category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if cat.parent_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Only top-level categories can be reordered; subcategories are always sorted alphabetically.",
        )

    siblings = (
        db.query(Category)
        .filter(Category.parent_id.is_(None))
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    idx = next((i for i, s in enumerate(siblings) if s.id == cat.id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Category not found")

    swap_idx = idx - 1 if payload.direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(siblings):
        # Already at the top/bottom — nothing to do, not an error.
        return cat

    # Swap positions in the list, then renumber everyone sequentially. A plain
    # value-swap between the two categories would silently no-op whenever they
    # shared a sort_order (e.g. right after the backfill migration, or two
    # categories both left at the column default) — renumbering the whole
    # list from the new order guarantees the click always moves something,
    # and keeps the gaps tidy as a side effect.
    siblings[idx], siblings[swap_idx] = siblings[swap_idx], siblings[idx]
    for i, s in enumerate(siblings):
        s.sort_order = i * 10

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    # prevent delete if has children
    child = db.query(Category).filter(Category.parent_id == cat.id).first()
    if child:
        raise HTTPException(status_code=400, detail="Cannot delete category with subcategories; delete or move children first")
    # prevent delete if has products
    from app.models.product import Product
    prod = db.query(Product).filter(Product.category_id == cat.id).first()
    if prod:
        raise HTTPException(status_code=400, detail="Cannot delete category with products")
    db.delete(cat)
    db.commit()
    return None
