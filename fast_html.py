from fasthtml.common import * 

db = database('data/auther.db')

class User:
    username: str
    pwd: str


class Book:
    id: int
    title: str
    auther: str
    price: int
    pages: int
    published: bool
    published_date: str


users = db.create(User, pk='username')
books = db.create(Book)


def lookup_user(u, p):
    try:
        user = users[u]
    except NotFoundError:
        user = users.insert(username=u, pwd=p)
    return user.pwd == p


auth_middleware = user_pwd_auth(
    lookup_user)


app = FastHTML(middleware=[auth_middleware],
               hdrs=(picolink,
                     Style(':root { --pico-font-size: 100%; }')))

route = app.route

id_curr = 'current-book'
def mk_input(**kw): return Input(**kw)
def clr_details(): return Div(hx_swap_oob='innerHTML', id=id_curr)
def tid(id): return f'book-{id}'


PER_PAGE = 5  


@route("/")
async def get(request, auth):
  
    page = int(request.query_params.get('page', 1))

    total_books = len(books())

    total_pages = (total_books + PER_PAGE - 1) // PER_PAGE

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_books = books()[start:end]

    search_bar = Input(
        id="q",
        placeholder="Search by title or author...",
        hx_get="/filter_books",
        target_id='book-rows')

    published_filter = CheckboxX(
        id="published_filter",
        label='Published Only',
        hx_get="/filter_books",
        target_id='book-rows',
        style="margin-bottom: 10px;"
    )

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    pagination = Div(
        A("Previous", href=f"/?page={prev_page}",
          style="margin-right: 10px;") if prev_page else '',
        A("Next", href=f"/?page={next_page}") if next_page else '',
        style="margin-top: 10px; text-align: center;"
    )

    add = Div(
        H4("Add Book"),
        Form(Group(
            mk_input(placeholder="Title", name="title",
                     id="title", required=True),
            mk_input(placeholder="Auther", name="auther", id="auther"),
            mk_input(placeholder="Price", type="number",
                     name="price", id="price"),
            mk_input(placeholder="Pages", type="number",
                     name="pages", id="pages"),
            mk_input(placeholder="Published Date", type="date",
                     name="published_date", id="published_date"),
            Button("Add")),
            CheckboxX(id="published", name="published", label='Published'),
            hx_post="/", target_id='book-rows', hx_swap="beforeend"

        )
    )

    card = Card(H4(f"Books (total {total_books} books)"),
                search_bar,
                published_filter,
                Table(
                    Thead(Tr(Th("Title"), Th("Auther"), Th("Price"), Th("Pages"), Th(
                        "Published"), Th("Published Date"), Th("Edit"))),
                    Tbody(*[book.__ft__()
                          for book in paginated_books], id='book-rows')
    ),
        header=add,
        footer=Div(pagination,
                   Div(id=id_curr)  
                   )
    )

    top = Grid(Div(A('logout', href=basic_logout(request)),
               style='text-align: right'))

    return Titled(f"Book Management (Page {page})", top, card)


@patch
def __ft__(self: Book):
    show = AX(self.title, f'/books/{self.id}', id_curr)
    edit = AX('edit', f'/edit/{self.id}', id_curr)
    dt = '✅ ' if self.title else ''
    return Tr(
        Td(dt, show), Td(self.auther), Td(self.price), Td(self.pages),
        Td(self.published), Td(self.published_date), Td(edit),
        id=tid(self.id)
    )


@route("/filter_books")
async def filter_books(request):
    q = request.query_params.get('q', None)
    published_filter = request.query_params.get('published_filter', None)
    page = int(request.query_params.get('page', 1))
    filtered_books = books()

    if q:
        filtered_books = [book for book in books() if q.lower(
        ) in book.title.lower() or q.lower() in book.auther.lower()]

    if published_filter:
        filtered_books = [book for book in filtered_books if book.published]


    total_books = len(filtered_books)
    total_pages = (total_books + PER_PAGE - 1) // PER_PAGE

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_books = filtered_books[start:end]

    if not paginated_books:
        return Tr(Td(
            "No books found", colspan=6,
            style="text-align: center; color: red;"))

    return Tr(
        *[book.__ft__() for book in paginated_books],
        id='book-rows'
    )


@route("/books/{id}")
async def delete(id: int):
    """Delete a book"""
    books.delete(id)
    return clr_details()


@route("/")
async def post(book: Book):
    return books.insert(book), mk_input(hx_swap_oob='true')


@route("/edit/{id}")
async def get(id: int):
    res = Div(
        H4("Edit Book"),
        Form(Group(Input(id="title"),
                   Input(id="auther"),
                   Input(id="price", type="number"),
                   Input(id="pages", type="number"),
                   Input(id="published_date", type="date"),
                   Button("Save")),
             Hidden(id="id"), CheckboxX(id="published", label='Published'),
             hx_put="/", target_id=tid(id), id="edit")
    )
    return fill_form(res, books[id])


@route("/")
async def put(book: Book):
    return books.upsert(book), clr_details()


@route("/books/{id}")
async def get(id: int):
    book = books[id]
    btn = Button('Delete Book', hx_delete=f'/books/{book.id}',
                 target_id=tid(book.id), hx_swap="outerHTML")
    btn.style = 'background-color: red; border: none;'
    return Div(H2(f"Book Title: {book.title}"),
               H6(f"Published: {"Yes" if book.published else "No"}"),
               btn)


serve()
