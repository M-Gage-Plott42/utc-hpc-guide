# Typeface Proof Specimen {.unnumbered .unlisted}

This review-only appendix compares the code-block typefaces at matched
perceived size. It is not part of the release candidate and will be removed
after one profile is selected. Inspect the characters at normal size and high
zoom, then compare indentation, punctuation, line endings, and interior
spaces after text extraction.

The first sample uses the regular face. The marker-bounded lines are also the
machine extraction sentinel; their four-space indentation and two-space
separator are intentional.

```text
REGULAR AMBIGUOUS GLYPHS
0 O o 1 l I | < > <= >= == != -> -- _ ~ \ / ' " ( ) [ ] { }
EXTRACTION-PROOF-START
root
    indented child
column-a  column-b
EXTRACTION-PROOF-END
```

The second sample requires the profile's pinned bold face and repeats the
ambiguous characters so weight does not hide a distinction.

```{.text .font-proof-bold}
BOLD AMBIGUOUS GLYPHS
0 O o 1 l I | < > <= >= == != -> -- _ ~ \ / ' " ( ) [ ] { }
```
