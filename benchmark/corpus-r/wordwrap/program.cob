      * cobol-equiv corpus: WORDWRAP (MIT licensed)
      * Fills words into lines of a given width. Semantic area: UNSTRING
      * with DELIMITED BY ALL SPACE, COUNT IN and WITH POINTER, STRING
      * WITH POINTER, reference modification to split long words,
      * PERFORM UNTIL loops nested two deep.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. WORDWRAP.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TEXT-FILE ASSIGN TO "TEXT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD TEXT-FILE.
       01 TEXT-REC.
          05 TX-WIDTH       PIC 99.
          05 TX-TEXT        PIC X(60).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-PTR            PIC 99.
       01 WS-WORD           PIC X(60).
       01 WS-WLEN           PIC 99.
       01 WS-LINE           PIC X(40).
       01 WS-LPTR           PIC 99.
       01 WS-USED           PIC 99.
       01 WS-START          PIC 99.
       01 WS-PART           PIC 99.
       01 WS-LINES          PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT TEXT-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ TEXT-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM WRAP-TEXT
               END-READ
           END-PERFORM
           CLOSE TEXT-FILE
           DISPLAY "LINES " WS-LINES
           STOP RUN.

       WRAP-TEXT.
           IF TX-WIDTH < 5 OR TX-WIDTH > 40
               DISPLAY "BAD WIDTH " TX-WIDTH
           ELSE
               DISPLAY "WIDTH " TX-WIDTH
               MOVE SPACES TO WS-LINE
               MOVE 0 TO WS-USED
               MOVE 1 TO WS-PTR
               PERFORM UNTIL WS-PTR > 60
                   MOVE SPACES TO WS-WORD
                   MOVE 0 TO WS-WLEN
                   UNSTRING TX-TEXT DELIMITED BY ALL SPACE
                       INTO WS-WORD COUNT IN WS-WLEN
                       WITH POINTER WS-PTR
                   END-UNSTRING
                   IF WS-WLEN > 0
                       PERFORM PLACE-WORD
                   END-IF
               END-PERFORM
               IF WS-USED > 0
                   PERFORM FLUSH-LINE
               END-IF
           END-IF.

       PLACE-WORD.
           MOVE 1 TO WS-START
           PERFORM UNTIL WS-WLEN - WS-START < TX-WIDTH
               IF WS-USED > 0
                   PERFORM FLUSH-LINE
               END-IF
               MOVE WS-WORD (WS-START:TX-WIDTH - 1) TO WS-LINE
               MOVE "-" TO WS-LINE (TX-WIDTH:1)
               MOVE TX-WIDTH TO WS-USED
               PERFORM FLUSH-LINE
               COMPUTE WS-START = WS-START + TX-WIDTH - 1
           END-PERFORM
           COMPUTE WS-PART = WS-WLEN - WS-START + 1
           IF WS-USED > 0 AND WS-USED + 1 + WS-PART > TX-WIDTH
               PERFORM FLUSH-LINE
           END-IF
           IF WS-USED = 0
               MOVE 1 TO WS-LPTR
           ELSE
               COMPUTE WS-LPTR = WS-USED + 2
           END-IF
           STRING WS-WORD (WS-START:WS-PART) DELIMITED BY SIZE
               INTO WS-LINE WITH POINTER WS-LPTR
           COMPUTE WS-USED = WS-LPTR - 1.

       FLUSH-LINE.
           ADD 1 TO WS-LINES
           DISPLAY "|" WS-LINE (1:TX-WIDTH) "|"
           MOVE SPACES TO WS-LINE
           MOVE 0 TO WS-USED.
