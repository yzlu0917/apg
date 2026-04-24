PDF=main.pdf

all: $(PDF)

$(PDF): main.tex sections/abstract.tex sections/introduction.tex sections/program.tex sections/results.tex sections/implications.tex sections/conclusion.tex references.bib neurips_2024.sty
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -C
