# IDocr
This Project is All about extracting the content from the ID card which can be used to on spot registration like things

My Flow of this project 


```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
Image --> Website --> Pillow image --> opencv --> EasyOCR --> extracted information --> again OCR for flipped text (90deg clock or counter clock wise) --> Extracted Information --> RegEX (Customised one for our clg - bitsathy) --> classified output --> google sheets (with timestamp)
```

