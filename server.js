const client = require("cheerio-httpcli");
let app = require("http")
  .createServer(handler)
  .listen(4000);
console.log("Bot server start!");
let fs = require("fs");
let url = require("url");
let http = require("https");
const XlsxPopulate = require("xlsx-populate");

let array = [];
let arrayc = [];
let io = require("socket.io").listen(app);
let num = 0;
let flag = 1;
io.sockets.on("connection", socket => {
  socket.on("test", item => {
    // console.log(item);
    client
      .fetch("https://www.verajohn.com/ja/game/european-roulette")
      .then(result => {
        // scraiping
        let data = result.$("title").text();
        let num = result.$("script").text();
        let box = {
          data: data,
          script: num
        };
      });

    console.log("data");
    socket.emit("title", "https://www.verajohn.com/ja/game/european-roulette");
    //let flag = 1 ;
    let id = setInterval(function() {
      cl();
      flag++;
      if (flag > item) {
        clearInterval(id);
        socket.emit("fin", "fin");
        console.log("fin");
      }
    }, 5000);
  });
});

function handler(req, res) {
  let q = url.parse(req.url, true);
  switch (q.pathname) {
    case "/":
      fs.readFile("./index.html", "UTF-8", function(err, data) {
        res.writeHead(200, { "Content-Type": "text/html" });
        res.write(data);
        res.end();
      });
      break;
    default:
      var file = __dirname + "/Test.xlsx";

      res.writeHead(200, {
        "Content-Disposition": "attachment; filename=" + file
      });

      var filestream = fs.createReadStream(file);
      filestream.pipe(res);
      break;
  }
}

//cerajohnのeuropian-rouletteに接続．
const cllack = "https://www.verajohn.com/ja/game/european-roulette";

// const XLSX = require("xlsx");
// const Utils = XLSX.utils; //
//const XlsxPopulate = require('xlsx-populate')
let N2 = 0; //all
let C4 = 0; //low
let C16 = 0; //high
let C7 = 0; //even
let C13 = 0; //odd
let D2 = 0; //green
let D8 = 0; //red
let D12 = 0; //black
let E6 = 0; //1st
let E10 = 0; //2nd
let E14 = 0; //3rd

let G4 = 0; //1
let J4 = 0; //2
let M4 = 0; //3
let G5 = 0; //4
let J5 = 0; //5
let M5 = 0; //6
let G6 = 0; //7
let J6 = 0; //8
let M6 = 0; //9
let G7 = 0; //10
let J7 = 0; //11
let M7 = 0; //12
let G8 = 0; //13
let J8 = 0; //14
let M8 = 0; //15
let G9 = 0; //16
let J9 = 0; //17
let M9 = 0; //18
let G10 = 0; //19
let J10 = 0; //20
let M10 = 0; //21
let G11 = 0; //22
let J11 = 0; //23
let M11 = 0; //24
let G12 = 0; //25
let J12 = 0; //26
let M12 = 0; //27
let G13 = 0; //28
let J13 = 0; //29
let M13 = 0; //30
let G14 = 0; //31
let J14 = 0; //32
let M14 = 0; //33
let G15 = 0; //34
let J15 = 0; //35
let M15 = 0; //36

function cl(num) {
  // const p = client.fetch("https://www.verajohn.com/ja/game/european-roulette")
  // .then((result) => {
  //   // scraiping

  //  let data = result.$("title").text()
  //   console.log("title is "+ data ) ;
  // //  let num = result.$("script").text() ;
  //   console.log("num"+num) ;
  num = Math.floor(Math.random() * 37);
  let box = judge(num);
  console.log(box);
  exe(box);
  // });
}

function judge(num) {
  let color = "black";
  let high_low = "low";
  let third = "1st";
  let twelve = "A";

  const red = [
    1,
    3,
    5,
    7,
    9,
    12,
    14,
    16,
    18,
    19,
    21,
    23,
    25,
    27,
    30,
    32,
    34,
    36
  ]; //18
  const black = [
    2,
    4,
    6,
    8,
    11,
    13,
    15,
    17,
    20,
    22,
    24,
    26,
    28,
    29,
    31,
    33,
    35
  ]; //18
  const green = [0];

  const Fst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]; //12
  const Snd = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]; //12
  const Srd = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]; //12

  const A = [1, 2, 3];
  const B = [4, 5, 6];
  const C = [7, 8, 9];
  const D = [10, 11, 12];
  const E = [13, 14, 15];
  const F = [16, 17, 18];
  const G = [19, 20, 21];
  const H = [22, 23, 24];
  const I = [25, 26, 27];
  const J = [28, 29, 30];
  const K = [31, 32, 33];
  const L = [34, 35, 36];

  //color
  if (red.indexOf(num) >= 0) {
    //redに存在する
    color = "red";
  } else if (num == 0) {
    color = "green";
  } else {
    color = "black";
  }

  //high&low
  if (num >= 19) {
    high_low = "high";
  } else {
    high_low = "low";
  }

  //1st,2nd,3rd
  if (Fst.indexOf(num) >= 0) {
    third = "1st";
  } else if (Snd.indexOf(num) >= 0) {
    third = "2nd";
  } else if (Srd.indexOf(num) >= 0) {
    third = "3rd";
  } else {
    third = "nothing";
  }

  //A,B,C
  if (A.indexOf(num) >= 0) {
    twelve = "A";
  } else if (B.indexOf(num) >= 0) {
    twelve = "B";
  } else if (C.indexOf(num) >= 0) {
    twelve = "C";
  } else if (D.indexOf(num) >= 0) {
    twelve = "D";
  } else if (E.indexOf(num) >= 0) {
    twelve = "E";
  } else if (F.indexOf(num) >= 0) {
    twelve = "F";
  } else if (G.indexOf(num) >= 0) {
    twelve = "G";
  } else if (H.indexOf(num) >= 0) {
    twelve = "H";
  } else if (I.indexOf(num) >= 0) {
    twelve = "I";
  } else if (J.indexOf(num) >= 0) {
    twelve = "J";
  } else if (K.indexOf(num) >= 0) {
    twelve = "K";
  } else if (L.indexOf(num) >= 0) {
    twelve = "L";
  } else {
    twelve = "nothing";
  }

  // console.log(" num : "+ num + "\n color : " + color + "\n high_low : " + high_low + "\n third : " + third + "\n twelve : " + twelve) ;
  let box = {
    num: num,
    color: color,
    high_low: high_low,
    third: third,
    twelve: twelve
  };
  return box;
}

function exe(box) {
  array.push(box.num);
  arrayc.push(box.color);
  cal(box);

  XlsxPopulate.fromFileAsync("./kajino.xlsx").then(book => {
    let Anum = 4;
    const sheet1 = book.sheet("シート1");
    for (let i = 0; i < array.length; i++) {
      sheet1.cell("A" + Anum).value(array[i]);
      sheet1.cell("B" + Anum).value(arrayc[i]);
      Anum++;
    }
    sheet1.cell("N2").value(N2);
    sheet1.cell("C4").value(C4);
    sheet1.cell("C16").value(C16);
    sheet1.cell("C7").value(C7);
    sheet1.cell("C13").value(C13);
    sheet1.cell("D2").value(D2);
    sheet1.cell("D8").value(D8);
    sheet1.cell("D12").value(D12);
    sheet1.cell("E6").value(E6);
    sheet1.cell("E10").value(E10);
    sheet1.cell("E14").value(E14);
    sheet1.cell("G4").value(G4);
    sheet1.cell("J4").value(J4);
    sheet1.cell("M4").value(M4);
    sheet1.cell("G5").value(G5);
    sheet1.cell("J5").value(J5);
    sheet1.cell("M5").value(M5);
    sheet1.cell("G6").value(G6);
    sheet1.cell("J6").value(J6);
    sheet1.cell("M6").value(M6);
    sheet1.cell("G7").value(G7);
    sheet1.cell("J7").value(J7);
    sheet1.cell("M7").value(M7);
    sheet1.cell("G8").value(G8);
    sheet1.cell("J8").value(J8);
    sheet1.cell("M8").value(M8);
    sheet1.cell("G9").value(G9);
    sheet1.cell("J9").value(J9);
    sheet1.cell("M9").value(M9);
    sheet1.cell("G10").value(G10);
    sheet1.cell("J10").value(J10);
    sheet1.cell("M10").value(M10);
    sheet1.cell("G11").value(G11);
    sheet1.cell("J11").value(J11);
    sheet1.cell("M11").value(M11);
    sheet1.cell("G12").value(G12);
    sheet1.cell("J12").value(J12);
    sheet1.cell("M12").value(M12);
    sheet1.cell("G13").value(G13);
    sheet1.cell("J13").value(J13);
    sheet1.cell("M13").value(M13);
    sheet1.cell("G14").value(G14);
    sheet1.cell("J14").value(J14);
    sheet1.cell("M14").value(M14);
    sheet1.cell("G15").value(G15);
    sheet1.cell("J15").value(J15);
    sheet1.cell("M15").value(M15);
    if (flag == 6) {
      sheet1.cell("D20").value(redbox.length);
      sheet1.cell("E20").value(blackbox.length);
    }
     var today = new Date();
    book.toFileAsync("./"+today+"Test.xlsx");
  });
  let a = box.num;
  console.log("exeから :" + a);
}

function cal(box) {
  N2++;
  //odd&even
  if (box.num == 0) {
  } else if (box.num % 2 == 0) {
    C7++;
  } else {
    C13++;
  }
  //color
  if (box.color == "black") {
    D12++;
  } else if (box.color == "red") {
    D8++;
  } else {
    D2++;
  }
  //low_high
  if (box.high_low == "high") {
    C16++;
  } else if (box.high_low == "low") {
    C4++;
  } else {
  }

  //1st,2nd,3rd
  if (box.third == "1st") {
    E6++;
  } else if (box.third == "2nd") {
    E10++;
  } else if (box.third == "3rd") {
    E14++;
  } else {
  }

  //num
  if (box.num == 1) {
    G4++;
  } else if (box.num == 2) {
    J4++;
  } else if (box.num == 3) {
    M4++;
  } else if (box.num == 4) {
    G5++;
  } else if (box.num == 5) {
    J5++;
  } else if (box.num == 6) {
    M5++;
  } else if (box.num == 7) {
    G6++;
  } else if (box.num == 8) {
    J6++;
  } else if (box.num == 9) {
    M6++;
  } else if (box.num == 10) {
    G7++;
  } else if (box.num == 11) {
    J7++;
  } else if (box.num == 12) {
    M7++;
  } else if (box.num == 13) {
    G8++;
  } else if (box.num == 14) {
    J8++;
  } else if (box.num == 15) {
    M8++;
  } else if (box.num == 16) {
    G9++;
  } else if (box.num == 17) {
    J9++;
  } else if (box.num == 18) {
    M9++;
  } else if (box.num == 19) {
    G10++;
  } else if (box.num == 20) {
    J10++;
  } else if (box.num == 21) {
    M10++;
  } else if (box.num == 22) {
    G11++;
  } else if (box.num == 23) {
    J11++;
  } else if (box.num == 24) {
    M11++;
  } else if (box.num == 25) {
    G12++;
  } else if (box.num == 26) {
    J12++;
  } else if (box.num == 27) {
    M12++;
  } else if (box.num == 28) {
    G13++;
  } else if (box.num == 29) {
    J13++;
  } else if (box.num == 30) {
    M13++;
  } else if (box.num == 31) {
    G14++;
  } else if (box.num == 32) {
    J14++;
  } else if (box.num == 33) {
    M14++;
  } else if (box.num == 34) {
    G15++;
  } else if (box.num == 35) {
    J15++;
  } else if (box.num == 36) {
    M15++;
  } else {
  }
}
