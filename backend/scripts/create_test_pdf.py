"""Create a test PDF document about Romanian financial instruments."""

import fitz  # PyMuPDF


def create_test_pdf():
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "Titluri de stat TEZAUR si FIDELIS\n\n"
        "Ce sunt titlurile de stat?\n\n"
        "Titlurile de stat sunt instrumente financiare emise de Ministerul "
        "Finantelor din Romania pentru a finanta deficitul bugetar. Ele "
        "reprezinta o forma de imprumut pe care statul il ia de la cetateni, "
        "oferind in schimb o dobanda fixa.\n\n"
        "TEZAUR\n\n"
        "Titlurile TEZAUR sunt destinate exclusiv persoanelor fizice rezidente "
        "in Romania. Caracteristici principale: Maturitate de 1 an, 3 ani sau "
        "5 ani. Dobanda fixa, platita la scadenta sau anual. Valoare nominala "
        "minima de 1 RON. Sunt 100% garantate de statul roman. Scutite de "
        "impozit pe venit.\n\n"
        "Avantaje TEZAUR: Nu exista risc de pierdere a capitalului investit. "
        "Dobanzile sunt mai mari decat la depozitele bancare. Scutire de impozit "
        "pe venit. Accesibile de la 1 RON.\n\n"
        "FIDELIS\n\n"
        "Titlurile FIDELIS sunt listate la Bursa de Valori Bucuresti (BVB). "
        "Pot fi tranzactionate pe piata secundara. Maturitate de 1-5 ani. "
        "Denominare in LEI sau EURO. Dobanda fixa, platita semestrial sub "
        "forma de cupon.\n\n"
        "Diferente: TEZAUR nu se tranzactioneaza pe bursa, FIDELIS da. "
        "TEZAUR scutit de impozit. FIDELIS impozitat cu 10% din 2023.\n\n"
        "Nu reprezinta recomandare de investitii conform MiFID II."
    )
    rect = fitz.Rect(72, 72, 540, 780)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    doc.save("/app/documents/test_tezaur_fidelis.pdf")
    doc.close()
    print("Test PDF created successfully")


if __name__ == "__main__":
    create_test_pdf()
