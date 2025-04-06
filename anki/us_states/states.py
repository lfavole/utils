from pathlib import Path


data = """\
Alabama¬Montgomery¬AL¬<img src="300px-Alabama_in_United_States.svg.png">¬<img src="US-AL.svg" style="border:1px solid black">
Alaska¬Juneau¬AK¬<img src="300px-Alaska_in_United_States_(US50).svg.png">¬<img src="US-AK.svg">
Arizona¬Phoenix¬AZ¬<img src="300px-Arizona_in_United_States.svg.png">¬<img src="US-AZ.svg">
Arkansas¬Little Rock¬AR¬<img src="300px-Arkansas_in_United_States.svg.png">¬<img src="US-AR.svg">
California¬Sacramento¬CA¬<img src="300px-California_in_United_States.svg.png">¬<img src="US-CA.svg" style="border:1px solid black">
Colorado¬Denver¬CO¬<img src="300px-Colorado_in_United_States.svg.png">¬<img src="US-CO.svg" style="border:1px solid black">
Connecticut¬Hartford¬CT¬<img src="300px-Connecticut_in_United_States_(zoom).svg.png">¬<img src="US-CT.svg">
Delaware¬Dover¬DE¬<img src="300px-Delaware_in_United_States_(zoom).svg.png">¬<img src="US-DE.svg">
Florida¬Tallahassee¬FL¬<img src="300px-Florida_in_United_States.svg.png">¬<img src="US-FL.svg" style="border:1px solid black">
Georgia¬Atlanta¬GA¬<img src="300px-Georgia_in_United_States.svg.png">¬<img src="US-GA.svg" style="border:1px solid black">
Hawaii¬Honolulu¬HI¬<img src="300px-Hawaii_in_United_States_(US50)_(+grid)_(zoom)_(W3).svg.png">¬<img src="US-HI.svg" style="border:1px solid black">
Idaho¬Boise¬ID¬<img src="300px-Idaho_in_United_States.svg.png">¬<img src="US-ID.svg">
Illinois¬Springfield¬IL¬<img src="300px-Illinois_in_United_States.svg.png">¬<img src="US-IL.svg" style="border:1px solid black">
Indiana¬Indianapolis¬IN¬<img src="300px-Indiana_in_United_States.svg.png">¬<img src="US-IN.svg">
Iowa¬Des Moines¬IA¬<img src="300px-Iowa_in_United_States.svg.png">¬<img src="US-IA.svg" style="border:1px solid black">
Kansas¬Topeka¬KS¬<img src="300px-Kansas_in_United_States.svg.png">¬<img src="US-KS.svg">
Kentucky¬Frankfort¬KY¬<img src="300px-Kentucky_in_United_States.svg.png">¬<img src="US-KY.svg">
Louisiana¬Baton Rouge¬LA¬<img src="300px-Louisiana_in_United_States.svg.png">¬<img src="US-LA.svg">
Maine¬Augusta¬ME¬<img src="300px-Maine_in_United_States.svg.png">¬<img src="US-ME.svg">
Maryland¬Annapolis¬MD¬<img src="300px-Maryland_in_United_States_(zoom).svg.png">¬<img src="US-MD.svg">
Massachusetts¬Boston¬MA¬<img src="300px-Massachusetts_in_United_States.svg.png">¬<img src="US-MA.svg" style="border:1px solid black">
Michigan¬Lansing¬MI¬<img src="300px-Michigan_in_United_States.svg.png">¬<img src="US-MI.svg">
Minnesota¬Saint Paul¬MN¬<img src="300px-Minnesota_in_United_States.svg.png">¬<img src="US-MN.svg">
Mississippi¬Jackson¬MS¬<img src="300px-Mississippi_in_United_States.svg.png">¬<img src="125px-Flag_of_Mississippi.svg.png">
Missouri¬Jefferson City¬MO¬<img src="300px-Missouri_in_United_States.svg.png">¬<img src="US-MO.svg" style="border:1px solid black">
Montana¬Helena¬MT¬<img src="300px-Montana_in_United_States.svg.png">¬<img src="US-MT.svg">
Nebraska¬Lincoln¬NE¬<img src="300px-Nebraska_in_United_States.svg.png">¬<img src="US-NE.svg">
Nevada¬Carson City¬NV¬<img src="300px-Nevada_in_United_States.svg.png">¬<img src="US-NV.svg">
New Hampshire¬Concord¬NH¬<img src="300px-New_Hampshire_in_United_States.svg.png">¬<img src="US-NH.svg">
New Jersey¬Trenton¬NJ¬<img src="300px-New_Jersey_in_United_States_(zoom).svg.png">¬<img src="US-NJ.svg">
New Mexico¬Santa Fe¬NM¬<img src="300px-New_Mexico_in_United_States.svg.png">¬<img src="US-NM.svg">
New York¬Albany¬NY¬<img src="300px-New_York_in_United_States.svg.png">¬<img src="US-NY.svg">
North Carolina¬Raleigh¬NC¬<img src="300px-North_Carolina_in_United_States.svg.png">¬<img src="US-NC.svg" style="border:1px solid black">
North Dakota¬Bismarck¬ND¬<img src="300px-North_Dakota_in_United_States.svg.png">¬<img src="US-ND.svg">
Ohio¬Columbus¬OH¬<img src="300px-Ohio_in_United_States.svg.png">¬<img src="US-OH.svg" style="border:1px solid black">
Oklahoma¬Oklahoma City¬OK¬<img src="300px-Oklahoma_in_United_States.svg.png">¬<img src="US-OK.svg">
Oregon¬Salem¬OR¬<img src="300px-Oregon_in_United_States.svg.png">¬<img src="US-OR.svg">
Pennsylvania¬Harrisburg¬PA¬<img src="300px-Pennsylvania_in_United_States.svg.png">¬<img src="US-PA.svg">
Rhode Island¬Providence¬RI¬<img src="300px-Rhode_Island_in_United_States_(zoom)_(extra_close).svg.png">¬<img src="US-RI.svg" style="border:1px solid black">
South Carolina¬Columbia¬SC¬<img src="300px-South_Carolina_in_United_States.svg.png">¬<img src="US-SC.svg">
South Dakota¬Pierre¬SD¬<img src="300px-South_Dakota_in_United_States.svg.png">¬<img src="US-SD.svg">
Tennessee¬Nashville¬TN¬<img src="300px-Tennessee_in_United_States.svg.png">¬<img src="US-TN.svg">
Texas¬Austin¬TX¬<img src="300px-Texas_in_United_States.svg.png">¬<img src="US-TX.svg" style="border:1px solid black">
Utah¬Salt Lake City¬UT¬<img src="300px-Utah_in_United_States.svg.png">¬<img src="US-UT.svg">
Vermont¬Montpelier¬VT¬<img src="300px-Vermont_in_United_States_(zoom).svg.png">¬<img src="US-VT.svg">
Virginia¬Richmond¬VA¬<img src="300px-Virginia_in_United_States.svg.png">¬<img src="US-VA.svg">
Washington¬Olympia¬WA¬<img src="300px-Washington_in_United_States.svg.png">¬<img src="US-WA.svg">
West Virginia¬Charleston¬WV¬<img src="300px-West_Virginia_in_United_States.svg.png">¬<img src="US-WV.svg">
Wisconsin¬Madison¬WI¬<img src="300px-Wisconsin_in_United_States.svg.png">¬<img src="US-WI.svg">
Wyoming¬Cheyenne¬WY¬<img src="300px-Wyoming_in_United_States.svg.png">¬<img src="US-WY.svg">
"""


def repl(el):
    return el.replace('src="', 'src="file:///C:/Users/Laurent/AppData/Roaming/Anki2/Laurent/collection.media/')


ret = """\
<style>
@page {
    margin: 5mm;
}
body {
    font-family: Montserrat, Arial, Helvetica, sans-serif;
    columns: 2;
}
h1 {
    margin: 0 0 0.2em 0;
    text-align: center;
}
table {
    border-collapse: collapse;
    width: 100%;
}
th, td {
    border: 1px solid black;
    padding: 4px;
    text-align: center;
}
td:nth-child(3) {
    font-size: 1.5em;
}
td:nth-last-child(2), td:last-child {
    padding: 0;
}
td:last-child {
    object-position: center center;
    width: 120px;
    max-width: 120px;
    overflow: hidden;
}
img {
    height: 72px;
    border: 0 !important;
}
</style>
<h1>États des États-Unis</h1>
<table>
<tr>
    <th>État</th>
    <th>Capitale</th>
    <th>Abrév.</th>
    <th>Carte</th>
    <th>Drapeau</th>
</tr>
"""
for line in data.splitlines():
    line = line.split("¬")
    ret += "<tr>" + "".join(f"<td>{repl(el)}</td>" for el in line) + "</tr>"
ret += "</table>"

with (Path(__file__).parent / "states.html").open("w") as f:
    f.write(ret)
