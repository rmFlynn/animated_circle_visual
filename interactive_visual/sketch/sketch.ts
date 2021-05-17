let depthCords:any
let zoomAmount:any
let dataCircles:any = []
let monthRadio:any;
let zoomRadio:any;
let ob_mon_string:any;
let ob_mon_num:any;
let focusDept:string = 'all';
let tittleH = 50;
let figH = 900;
let figW = 550;
let legendW = 250;
let top_bias = 50
let months:any = [];
let legend:any = [];

function setup() {
  createCanvas(figW + legendW, tittleH + figH).parent('canvas');
  setSliderValues();
  populate_objects();
  setZoomAmount()
  months[0] = new Title(7, 'July');
  months[1] = new Title(8, 'August');
  months[2] = new Title(9, 'September');
}
class LegendLine{
  name:string
  colo:any
  loca:number
  spaceing = figH / 20
  size = 40
  constructor(name:string, colo:any, loca:number){
    this.name = name
    this.colo = colo
    this.loca = loca +2
  }
  show(){
    push()
    translate(figW, tittleH)
    var strokeColo = this.colo;
    var fillColo = this.colo;
    fillColo.setAlpha(200);
    fill(fillColo);
    stroke(strokeColo);
    strokeWeight(2);
    circle(20, this.spaceing * this.loca, this.size);
    fill(255);
    textAlign(LEFT)
    textSize(20)
    strokeWeight(0)
    text(this.name, 50, this.spaceing * this.loca + 10)
    pop()
  }
}
function draw() {
  background(0)
  for (var i = 0; i < months.length; i++) {
    months[i].show()
  }
  for (var i = 0; i < legend.length; i++) {
    legend[i].show()
  }
  push()
  translate(0, tittleH)
  for (var i = 0; i < dataCircles.length; i++) {
    if(dataCircles[i].level == 0){
      dataCircles[i].show();
    }
  }
  for (var i = 0; i < dataCircles.length; i++) {
    if(dataCircles[i].level == 1){
      dataCircles[i].show();
    }
  }
  for (var i = 0; i < dataCircles.length; i++) {
    if(dataCircles[i].level == 2){
      dataCircles[i].show();
    }
  }
  for (var i = 0; i < dataCircles.length; i++) {
    if(dataCircles[i].level == 2){
      dataCircles[i].showNames();
    }
  }
  pop()
}
class Title{
  name: string;
  num:number;
  x:number;
  y:number;
  xTarg:number;
  cent:number;
  left:number;
  right:number;
  constructor(num:number, name:string){
    this.name = name;
    this.num = num;
    this.y = tittleH;

    this.cent = width/2;
    this.left = -width * 2;
    this.right = width * 2;
    this.set_target();
    this.x = this.xTarg;
  }
  set_target(){
    var n = monthRadio.value();
    if(this.num < n)
    {
      this.xTarg = this.left;
    }
    else if(this.num == n)
    {
      this.xTarg = this.cent;
    }
    else
    {
      this.xTarg = this.right;
    }
  }
  show(){
    fill(255);
    textAlign(CENTER);
    textSize(28);
    strokeWeight(0);
    this.set_target()
    text(this.name, this.x, this.y);
    this.x = deltaMath(this.x, this.xTarg);
  }
}
function setZoomAmount(){
  zoomAmount = {
    0: {
      7: 15,
      8: 15,
      9: 15,
    },
    1: {},
    2: {},
    3: {}
  }
  var depthMap: { [name: string]: number } = {'1': 1, '3': 2,'5/6': 3}
  var d:number
  for (var i = 0; i < dataCircles.length; i++) {
    if(dataCircles[i].level == 0){
      d = depthMap[dataCircles[i].depth]
      for (let key in dataCircles[i].circleArgs) {
          zoomAmount[d][key] = (figW - 70)/ (dataCircles[i].circleArgs[key][2] * 2 )
      }
    }
  }
  for (var i = 0; i < dataCircles.length; i++) {
    dataCircles[i].set_zoom()
  }

}

function setSliderValues(){

  monthRadio = createRadio().parent('control1')
  monthRadio.option(7, 'July      ')
  monthRadio.option(8, 'August      ')
  monthRadio.option(9, 'September     ')
  monthRadio.selected('7')
  monthRadio.attribute('name', 'month')

  // zoomSlider = createSlider(0, 3, 1, 1).parent('control2');
  zoomRadio = createRadio().parent('control2')
  zoomRadio.option(0, 'All Depths     ')
  zoomRadio.option(1, 'Depth 1     ')
  zoomRadio.option(2, 'Depth 3     ')
  zoomRadio.option(3, 'Depth 5/6     ')
  zoomRadio.selected('0')
  zoomRadio.attribute('name', 'zoom')

  depthCords = {
    0: {
      '1':  [figW/2, (figH/4)*1 - top_bias],
      '3':  [figW/2, (figH/4)*2 - (top_bias/2)],
      '5/6':[figW/2, (figH/4)*3]
    },
    1: {
      '1':  [figW/2, (figH/2)*1],
      '3':  [figW/2, (figH/2)*2 + figH],
      '5/6':[figW/2, (figH/2)*3 + figH]
    },
    2: {
      '1':  [figW/2, (figH/2)*1 - figH],
      '3':  [figW/2, (figH/2)],
      '5/6':[figW/2, (figH/2)*3 + figH]
    },
    3: {
      '1':  [figW/2, (figH/2)*1 - 2 * figH],
      '3':  [figW/2, (figH/2)*2 - 2 * figH],
      '5/6':[figW/2, (figH/2)]
    },
  }
}
class DataCirc{
  xCord:any
  yCord:any
  zoom:number
  flareAmount:number = ceil(50);
  diameter:number = 10;
  flareWeight:number = 3;
  diameterFinal:number;
  circleArgs:any;
  x:number = 0;
  y:number = 0;
  r:number = 0;
  name:string;
  showName:any
  depth:string;
  level:number;
  colo:any;
  state:number = 0;
  delay:number;
  ball:any;
  nameY:any;
  alpha:number = 255;
  constructor(name:string, depth:string, level:number, colo:any, circleArgs:any, showName:any, nameY:any){
    this.name = name;
    this.depth = depth;
    this.nameY = nameY;
    this.showName = showName
    this.level = level
    this.circleArgs = circleArgs
    this.x = circleArgs[monthRadio.value()][0]
    this.y = circleArgs[monthRadio.value()][1]
    this.r = circleArgs[monthRadio.value()][2]
    this.colo = colo;
    this.xCord = depthCords[zoomRadio.value()][this.depth][0]
    this.yCord = depthCords[zoomRadio.value()][this.depth][1]
    if(level == 0){
      this.alpha = 1
    }else if(level == 1){
      this.alpha = 100
    }else if(level == 2){
      this.alpha = 200
    }
  }
  set_zoom(){
    this.zoom = zoomAmount[zoomRadio.value()][monthRadio.value()]
  }
  show(){
    push()
    translate(this.xCord, this.yCord)
    var strokeColo = this.colo;
    var fillColo = this.colo;
    if(this.level == 0){
      fill(255);
      strokeColo = color(250);
      fillColo = color(250);
    }
    fillColo.setAlpha(this.alpha);
    fill(fillColo);
    stroke(strokeColo);
    strokeWeight(2);
    var z = this.zoom
    circle(this.x * z, this.y * z, 2 * this.r * z);
    if(this.level == 0){
      push()
      strokeWeight(1);
      fill(255)
      textSize(21)
      translate(( z * (this.x - this.r)) - 10, this.y)
      rotate(radians(270))
      text("Depth: " + this.depth, 0,0)
      pop()
    }
    pop()
    this.x = deltaMath(this.x, this.circleArgs[monthRadio.value()][0])
    this.y = deltaMath(this.y, this.circleArgs[monthRadio.value()][1])
    this.r = deltaMath(this.r, this.circleArgs[monthRadio.value()][2])
    this.xCord = deltaMath(this.xCord, depthCords[zoomRadio.value()][this.depth][0])
    this.yCord = deltaMath(this.yCord, depthCords[zoomRadio.value()][this.depth][1])
    this.zoom = deltaMath(this.zoom, zoomAmount[zoomRadio.value()][monthRadio.value()])
  }
  showNames(){
    push()
    translate(this.xCord, this.yCord)
    var z = this.zoom
    if(this.showName[monthRadio.value()]){
      fill(255);
      textAlign(LEFT)
      textSize(12)
      strokeWeight(0)
      var y = (this.y * z) + ((this.nameY[monthRadio.value()] - this.y) * 14)
      text(this.name, this.x * z, y)
    }
    pop()
  }
}
function deltaMath(val:number, tar:number, delta:number=0.05){
  var change = (tar - val) * delta
  if(change < delta && change > -delta){
    return(tar);
  }
  return(val + change);
}
