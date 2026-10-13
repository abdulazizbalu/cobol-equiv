      * cobol-equiv corpus: NAMEFMT (MIT licensed)
      * Reorders "LAST,FIRST MIDDLE" names. Semantic area: reference
      * modification with variable start and length as sender and as
      * receiver, character scanning loops, INSPECT CONVERTING on a
      * reference-modified item.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. NAMEFMT.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT NAME-FILE ASSIGN TO "NAMES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD NAME-FILE.
       01 NAME-REC          PIC X(30).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-TEXT           PIC X(30).
       01 WS-LEN            PIC 99.
       01 WS-COMMA          PIC 99.
       01 WS-S              PIC 99.
       01 WS-I              PIC 99.
       01 WS-P              PIC 99.
       01 WS-N              PIC 99.
       01 WS-WORDS          PIC 99.
       01 WS-OUT            PIC X(40).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT NAME-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ NAME-FILE INTO WS-TEXT
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM FORMAT-NAME
               END-READ
           END-PERFORM
           CLOSE NAME-FILE
           STOP RUN.

       FORMAT-NAME.
           MOVE 30 TO WS-LEN
           PERFORM UNTIL WS-LEN = 0
                   OR WS-TEXT (WS-LEN:1) NOT = SPACE
               SUBTRACT 1 FROM WS-LEN
           END-PERFORM
           IF WS-LEN = 0
               DISPLAY "EMPTY"
           ELSE
               MOVE 0 TO WS-COMMA
               PERFORM VARYING WS-I FROM 1 BY 1
                       UNTIL WS-I > WS-LEN OR WS-COMMA > 0
                   IF WS-TEXT (WS-I:1) = ","
                       MOVE WS-I TO WS-COMMA
                   END-IF
               END-PERFORM
               IF WS-COMMA < 2 OR WS-COMMA = WS-LEN
                   DISPLAY "NO SPLIT " WS-TEXT (1:WS-LEN)
               ELSE
                   COMPUTE WS-S = WS-COMMA + 1
                   PERFORM UNTIL WS-S > WS-LEN
                           OR WS-TEXT (WS-S:1) NOT = SPACE
                       ADD 1 TO WS-S
                   END-PERFORM
                   IF WS-S > WS-LEN
                       DISPLAY "NO SPLIT " WS-TEXT (1:WS-LEN)
                   ELSE
                       PERFORM BUILD-OUTPUT
                   END-IF
               END-IF
           END-IF.

       BUILD-OUTPUT.
           MOVE SPACES TO WS-OUT
           COMPUTE WS-N = WS-LEN - WS-S + 1
           MOVE WS-TEXT (WS-S:WS-N) TO WS-OUT (1:WS-N)
           INSPECT WS-OUT (1:1) CONVERTING
               "abcdefghijklmnopqrstuvwxyz" TO
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
           COMPUTE WS-P = WS-N + 2
           COMPUTE WS-N = WS-COMMA - 1
           MOVE WS-TEXT (1:WS-N) TO WS-OUT (WS-P:WS-N)
           ADD WS-N TO WS-P
           SUBTRACT 1 FROM WS-P
           MOVE 1 TO WS-WORDS
           PERFORM VARYING WS-I FROM 2 BY 1 UNTIL WS-I > WS-P
               IF WS-OUT (WS-I:1) NOT = SPACE
                       AND WS-OUT (WS-I - 1:1) = SPACE
                   ADD 1 TO WS-WORDS
               END-IF
           END-PERFORM
           DISPLAY "[" WS-OUT (1:WS-P) "] " WS-WORDS.
