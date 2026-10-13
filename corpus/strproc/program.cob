      * cobol-equiv corpus: STRPROC (MIT licensed)
      * Text handling. Semantic area: UNSTRING with several
      * delimiters, COUNT IN, POINTER, TALLYING and OVERFLOW;
      * INSPECT TALLYING / REPLACING / CONVERTING; STRING with
      * POINTER and OVERFLOW.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. STRPROC.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LINE-FILE ASSIGN TO "LINES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD LINE-FILE.
       01 LINE-REC.
          05 LN-TEXT        PIC X(30).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-COMMAS         PIC 99.
       01 WS-LEAD-SPACES    PIC 99.
       01 WS-AS             PIC 99.
       01 WS-F1             PIC X(8).
       01 WS-F2             PIC X(8).
       01 WS-F3             PIC X(6).
       01 WS-C1             PIC 99.
       01 WS-C2             PIC 99.
       01 WS-D1             PIC X.
       01 WS-PTR            PIC 99.
       01 WS-NF             PIC 99.
       01 WS-UOVF           PIC X.
       01 WS-OUT            PIC X(16).
       01 WS-OPTR           PIC 99.
       01 WS-SOVF           PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT LINE-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ LINE-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM DO-LINE
               END-READ
           END-PERFORM
           CLOSE LINE-FILE
           STOP RUN.

       DO-LINE.
           MOVE 0 TO WS-COMMAS WS-LEAD-SPACES WS-AS WS-NF WS-C1 WS-C2
           INSPECT LN-TEXT TALLYING WS-COMMAS FOR ALL ","
                                    WS-LEAD-SPACES FOR LEADING " "
           INSPECT LN-TEXT TALLYING WS-AS FOR ALL "A"
               BEFORE INITIAL ","
           MOVE SPACES TO WS-F1 WS-F2 WS-F3 WS-D1
           MOVE "N" TO WS-UOVF WS-SOVF
           MOVE 1 TO WS-PTR
           UNSTRING LN-TEXT DELIMITED BY "," OR ALL " "
               INTO WS-F1 DELIMITER IN WS-D1 COUNT IN WS-C1
                    WS-F2 COUNT IN WS-C2
                    WS-F3
               WITH POINTER WS-PTR
               TALLYING IN WS-NF
               ON OVERFLOW MOVE "Y" TO WS-UOVF
           END-UNSTRING
           INSPECT WS-F1 REPLACING ALL "A" BY "4"
                                   LEADING "0" BY "*"
           INSPECT WS-F2 CONVERTING "ABCDE" TO "abcde"
           INSPECT WS-F3 REPLACING CHARACTERS BY "#"
               AFTER INITIAL "B"
           MOVE SPACES TO WS-OUT
           MOVE 1 TO WS-OPTR
           STRING WS-F2 DELIMITED BY SPACE
                  "/" DELIMITED BY SIZE
                  WS-F1 DELIMITED BY " "
                  "/" DELIMITED BY SIZE
                  WS-F3 DELIMITED BY SIZE
               INTO WS-OUT WITH POINTER WS-OPTR
               ON OVERFLOW MOVE "Y" TO WS-SOVF
           END-STRING
           DISPLAY WS-COMMAS " " WS-LEAD-SPACES " " WS-AS " "
                   WS-NF " " WS-PTR " " WS-UOVF " "
                   "[" WS-F1 "][" WS-D1 "]" WS-C1
                   "[" WS-F2 "]" WS-C2 "[" WS-F3 "] "
                   "[" WS-OUT "] " WS-OPTR " " WS-SOVF.
