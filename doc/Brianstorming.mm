<map version="freeplane 1.12.1">
<!--To view this file, download free mind mapping software Freeplane from https://www.freeplane.org -->
<node TEXT="Detection Model" FOLDED="false" ID="ID_696401721" CREATED="1610381621824" MODIFIED="1751030509863" STYLE="oval">
<font SIZE="18"/>
<hook NAME="MapStyle" zoom="0.9090909">
    <properties edgeColorConfiguration="#808080ff,#ff0000ff,#0000ffff,#00ff00ff,#ff00ffff,#00ffffff,#7c0000ff,#00007cff,#007c00ff,#7c007cff,#007c7cff,#7c7c00ff" show_tags="UNDER_NODES" associatedTemplateLocation="template:/standard-1.6.mm" fit_to_viewport="false" show_icons="BESIDE_NODES"/>
    <tags category_separator="::"/>

<map_styles>
<stylenode LOCALIZED_TEXT="styles.root_node" STYLE="oval" UNIFORM_SHAPE="true" VGAP_QUANTITY="24 pt">
<font SIZE="24"/>
<stylenode LOCALIZED_TEXT="styles.predefined" POSITION="bottom_or_right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="default" ID="ID_271890427" ICON_SIZE="12 pt" COLOR="#000000" STYLE="fork">
<arrowlink SHAPE="CUBIC_CURVE" COLOR="#000000" WIDTH="2" TRANSPARENCY="200" DASH="" FONT_SIZE="9" FONT_FAMILY="SansSerif" DESTINATION="ID_271890427" STARTARROW="NONE" ENDARROW="DEFAULT"/>
<font NAME="SansSerif" SIZE="10" BOLD="false" ITALIC="false"/>
<richcontent TYPE="DETAILS" CONTENT-TYPE="plain/auto"/>
<richcontent TYPE="NOTE" CONTENT-TYPE="plain/auto"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.details"/>
<stylenode LOCALIZED_TEXT="defaultstyle.tags">
<font SIZE="10"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.attributes">
<font SIZE="9"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.note" COLOR="#000000" BACKGROUND_COLOR="#ffffff" TEXT_ALIGN="LEFT"/>
<stylenode LOCALIZED_TEXT="defaultstyle.floating">
<edge STYLE="hide_edge"/>
<cloud COLOR="#f0f0f0" SHAPE="ROUND_RECT"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.selection" BACKGROUND_COLOR="#afd3f7" BORDER_COLOR_LIKE_EDGE="false" BORDER_COLOR="#afd3f7"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.user-defined" POSITION="bottom_or_right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="styles.topic" COLOR="#18898b" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subtopic" COLOR="#cc3300" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subsubtopic" COLOR="#669900">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.important" ID="ID_67550811">
<icon BUILTIN="yes"/>
<arrowlink COLOR="#003399" TRANSPARENCY="255" DESTINATION="ID_67550811"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.flower" COLOR="#ffffff" BACKGROUND_COLOR="#255aba" STYLE="oval" TEXT_ALIGN="CENTER" BORDER_WIDTH_LIKE_EDGE="false" BORDER_WIDTH="22 pt" BORDER_COLOR_LIKE_EDGE="false" BORDER_COLOR="#f9d71c" BORDER_DASH_LIKE_EDGE="false" BORDER_DASH="CLOSE_DOTS" MAX_WIDTH="6 cm" MIN_WIDTH="3 cm"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.AutomaticLayout" POSITION="bottom_or_right" STYLE="bubble">
<stylenode LOCALIZED_TEXT="AutomaticLayout.level.root" COLOR="#000000" STYLE="oval" SHAPE_HORIZONTAL_MARGIN="10 pt" SHAPE_VERTICAL_MARGIN="10 pt">
<font SIZE="18"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,1" COLOR="#0033ff">
<font SIZE="16"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,2" COLOR="#00b439">
<font SIZE="14"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,3" COLOR="#990000">
<font SIZE="12"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,4" COLOR="#111111">
<font SIZE="10"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,5"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,6"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,7"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,8"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,9"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,10"/>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,11"/>
</stylenode>
</stylenode>
</map_styles>
</hook>
<hook NAME="AutomaticEdgeColor" COUNTER="7" RULE="ON_BRANCH_CREATION"/>
<node TEXT="Scope" POSITION="bottom_or_right" ID="ID_961084349" CREATED="1751030496068" MODIFIED="1751030509859" HGAP_QUANTITY="53.75 pt" VSHIFT_QUANTITY="-148.5 pt">
<edge COLOR="#ff0000"/>
<node TEXT="1. Detection of individual train waggons" ID="ID_1965524896" CREATED="1751030502876" MODIFIED="1751030543514"/>
<node TEXT="2. detection of waggons consists/individual trains" ID="ID_876324544" CREATED="1751030543910" MODIFIED="1751030569061"/>
<node TEXT="3. detection of specific waggons/trains via visual marks" ID="ID_536379398" CREATED="1751030569632" MODIFIED="1751030586059">
<node TEXT="Goal: track goods waggons for shunting operation" ID="ID_401752830" CREATED="1751030592406" MODIFIED="1751030611808"/>
</node>
</node>
<node TEXT="Conciderations" POSITION="bottom_or_right" ID="ID_1280771020" CREATED="1751030499520" MODIFIED="1751030791638" HGAP_QUANTITY="103.25 pt" VSHIFT_QUANTITY="64.5 pt">
<edge COLOR="#0000ff"/>
<node TEXT="" ID="ID_1047335971" CREATED="1751030755255" MODIFIED="1751030755255">
<hook NAME="FirstGroupNode"/>
</node>
<node TEXT="Single camera is fixed" ID="ID_330370873" CREATED="1751030635540" MODIFIED="1751030644496"/>
<node TEXT="Camera aperture and focal length is known" ID="ID_1533476447" CREATED="1751030726265" MODIFIED="1751030741982"/>
<node TEXT="" ID="ID_1121193342" CREATED="1751030755251" MODIFIED="1751030755253">
<hook NAME="SummaryNode"/>
<hook NAME="AlwaysUnfoldedNode"/>
<node TEXT="use of trigonometry" ID="ID_1226199886" CREATED="1751030755256" MODIFIED="1751030769299"/>
</node>
<node TEXT="track is 2D only(for the time being)" ID="ID_774506421" CREATED="1751030644893" MODIFIED="1751030695863">
<font ITALIC="false"/>
</node>
<node TEXT="Even lighting" ID="ID_439963912" CREATED="1751030704131" MODIFIED="1751030707668"/>
</node>
<node TEXT="Methods" POSITION="top_or_left" ID="ID_1384979724" CREATED="1751030796353" MODIFIED="1751031136509" HGAP_QUANTITY="71 pt" VSHIFT_QUANTITY="-111.75 pt">
<edge COLOR="#00ff00"/>
<node TEXT="Bounding boxes/Object detection" ID="ID_598005857" CREATED="1751030801377" MODIFIED="1751030812222">
<node TEXT="e.g. YOLO" ID="ID_1837573448" CREATED="1751030812948" MODIFIED="1751030816055"/>
<node TEXT="get a bounding box around a waggon to assess position" ID="ID_1276434738" CREATED="1751030816657" MODIFIED="1751030852000"/>
<node TEXT="orientation isnt detectable from the bbox" ID="ID_1029292339" CREATED="1751030852611" MODIFIED="1751030874867"/>
<node TEXT="directly apporaching train would get larger bbox with gaining pos inaccuracy" ID="ID_1663086026" CREATED="1751030913015" MODIFIED="1751030943983"/>
</node>
<node TEXT="Image segmentation" ID="ID_1772669890" CREATED="1751030950713" MODIFIED="1751030954553">
<node TEXT="similar considerations to object detection" ID="ID_593686628" CREATED="1751030955227" MODIFIED="1751030969773"/>
<node TEXT="get pos similarly to bbox" ID="ID_1731443023" CREATED="1751030974223" MODIFIED="1751031041963"/>
<node TEXT="no orientation" ID="ID_254103063" CREATED="1751031053431" MODIFIED="1751031056622"/>
</node>
<node TEXT="Keypoint detection" ID="ID_1467551864" CREATED="1751031057785" MODIFIED="1751031061269">
<node TEXT="get exact position of front and end" ID="ID_1942389110" CREATED="1751031068030" MODIFIED="1751031091296"/>
</node>
</node>
<node TEXT="Literature review" POSITION="top_or_left" ID="ID_734946314" CREATED="1751031137510" MODIFIED="1751031140766">
<edge COLOR="#ff00ff"/>
<node TEXT="OpenPose" ID="ID_848676758" CREATED="1751035464848" MODIFIED="1751281257441">
<arrowlink DESTINATION="ID_1433957451"/>
<node TEXT="Used VGG-19 head(10 layers) for feature maps" ID="ID_1422321316" CREATED="1751035467060" MODIFIED="1751035489978"/>
<node TEXT="uses labeld data" ID="ID_1948569186" CREATED="1751035769542" MODIFIED="1751035774980"/>
<node TEXT="adapt architecture to self supervision" ID="ID_790859564" CREATED="1751035779087" MODIFIED="1751035786920"/>
<node TEXT="Idea: Send MMR vids through VGG and use feature maps" ID="ID_1535020279" CREATED="1751035683968" MODIFIED="1751035700007">
<node TEXT="are there any important features on the trains(eg is the model capable of detecting)" ID="ID_1946522612" CREATED="1751035700769" MODIFIED="1751035724097"/>
<node TEXT="if no model sneeds fine tuning" ID="ID_916080031" CREATED="1751035725115" MODIFIED="1751035731612"/>
</node>
</node>
<node TEXT="AutoLink" ID="ID_1497709558" CREATED="1751035814232" MODIFIED="1751035816400">
<node TEXT="Self supervised keypoint linking" ID="ID_1742562533" CREATED="1751035816706" MODIFIED="1751035823639"/>
<node TEXT="uses single image" ID="ID_423240575" CREATED="1751035824216" MODIFIED="1751035828077">
<node TEXT="not eeded as we have video data" ID="ID_828819151" CREATED="1751035829358" MODIFIED="1751035838210"/>
<node TEXT="need to read more how self sup generated diff loss" ID="ID_1272368338" CREATED="1751035879573" MODIFIED="1751035891888"/>
</node>
</node>
<node TEXT="SimCC" ID="ID_1596253575" CREATED="1751036026805" MODIFIED="1751281248957">
<arrowlink DESTINATION="ID_1433957451"/>
<node TEXT="coordinate disjunct keypoint estimation" ID="ID_519527981" CREATED="1751280928771" MODIFIED="1751280937419"/>
<node TEXT="pre-labeld" ID="ID_35929397" CREATED="1751281080284" MODIFIED="1751281084551"/>
</node>
<node TEXT="Dundar et Al" ID="ID_1699193581" CREATED="1751281965192" MODIFIED="1751281975638">
<node TEXT="Multi stage segmentation of subject using maskign + future frame" ID="ID_245371819" CREATED="1751281969335" MODIFIED="1751281997086"/>
<node TEXT="expansion to ANY self supervised method" ID="ID_199273373" CREATED="1751282056702" MODIFIED="1751282063296"/>
</node>
</node>
<node TEXT="training methods" POSITION="top_or_left" ID="ID_499473960" CREATED="1751281091345" MODIFIED="1751281095217">
<edge COLOR="#7c0000"/>
<node TEXT="pre-labled" ID="ID_1433957451" CREATED="1751281095601" MODIFIED="1751281098141"/>
<node TEXT="self-supervised" ID="ID_1434776005" CREATED="1751281098880" MODIFIED="1751281104194"/>
</node>
<node TEXT="backbone models" POSITION="top_or_left" ID="ID_881070070" CREATED="1751281108562" MODIFIED="1751281112482">
<edge COLOR="#00007c"/>
<node TEXT="TokenPose" ID="ID_1329150261" CREATED="1751281113990" MODIFIED="1751281146928">
<node TEXT="encode keypoints as tokents to use attention between them" ID="ID_1272414275" CREATED="1751281360395" MODIFIED="1751281379525"/>
<node TEXT="requires CNN feature maps" ID="ID_1218864217" CREATED="1751281804218" MODIFIED="1751281810750"/>
<node TEXT="symetric features may cause problems" ID="ID_910379154" CREATED="1751281817848" MODIFIED="1751281835797"/>
</node>
<node TEXT="HRNet" ID="ID_1909789037" CREATED="1751281147476" MODIFIED="1751281149924">
<node TEXT="U-net like" ID="ID_1020494728" CREATED="1751281191204" MODIFIED="1751281201164"/>
</node>
</node>
<node TEXT="Tasks" POSITION="top_or_left" ID="ID_434817489" CREATED="1751034255293" MODIFIED="1751034256980">
<edge COLOR="#00ffff"/>
<node TEXT="create training data" ID="ID_389933166" CREATED="1751034258225" MODIFIED="1751034264242">
<node TEXT="supervised" ID="ID_104061711" CREATED="1751034359995" MODIFIED="1751034365969">
<node TEXT="place keypoints on train" POSITION="top_or_left" ID="ID_1459072616" CREATED="1751034270089" MODIFIED="1751034288721"/>
<node TEXT="check validity of background segmentation using pixel value mode" POSITION="top_or_left" ID="ID_1422660989" CREATED="1751034328182" MODIFIED="1751034343725"/>
</node>
<node TEXT="self supervised" ID="ID_709499170" CREATED="1751034373136" MODIFIED="1751034376073"/>
</node>
<node TEXT="" ID="ID_732633236" CREATED="1751035243059" MODIFIED="1751035243059"/>
<node TEXT="create model arhcitecture" ID="ID_1898489031" CREATED="1751034264877" MODIFIED="1751034268976">
<node TEXT="Keypoint matching" ID="ID_1723411978" CREATED="1751035244951" MODIFIED="1751035249052">
<node TEXT="Pose estimation requires the matchin of specific keypoints to a seceleton" ID="ID_1851622403" CREATED="1751035249449" MODIFIED="1751035266733"/>
<node TEXT="Humans only have &quot;unique&quot; keypoints (left elbow), wagons on trains may symetrical and are of lesser variance." ID="ID_1625542627" CREATED="1751035267337" MODIFIED="1751035456241"/>
</node>
<node TEXT="Sub1: Finetune CNN to trains" ID="ID_134841034" CREATED="1751035457615" MODIFIED="1751294271841">
<node TEXT="datasets include only &apos;bullet train&apos; label and low accuracy on model trains" ID="ID_486941431" CREATED="1751294274640" MODIFIED="1751294308183"/>
</node>
<node TEXT="Sub2: train detector/Train instance detector" ID="ID_446241877" CREATED="1751320400960" MODIFIED="1751320420104">
<node TEXT="" ID="ID_1844098880" CREATED="1751320404738" MODIFIED="1751320404738"/>
</node>
</node>
<node TEXT="Analyze Keypoint decriptor features" ID="ID_1570435242" CREATED="1755340960177" MODIFIED="1755340982438">
<node TEXT="Create an in/outgroup of train keypoints and view their descriptor features" ID="ID_1658618689" CREATED="1755340982921" MODIFIED="1755341005477"/>
<node TEXT="identify if a keypoint is in group" ID="ID_1129583860" CREATED="1755341006402" MODIFIED="1755341020759">
<node TEXT="Keypoint in ingroup if it is withing the interpotated mask of a train" ID="ID_715134063" CREATED="1755341030195" MODIFIED="1755341051365"/>
</node>
<node TEXT="analyse features" ID="ID_1202394607" CREATED="1755341021242" MODIFIED="1755341029463">
<node TEXT="PCA of region around the keypoint" ID="ID_1296563632" CREATED="1755341053295" MODIFIED="1755341072758"/>
</node>
</node>
<node TEXT="Do training run" ID="ID_1791928967" CREATED="1755855580796" MODIFIED="1755855585088">
<node TEXT="Generate data" ID="ID_4813987" CREATED="1755855585571" MODIFIED="1755855588571">
<node TEXT="1. Generate Pseudo lables" ID="ID_1068280850" CREATED="1755855589480" MODIFIED="1755855597498">
<node TEXT="Identify already annotated images" ID="ID_1781551591" CREATED="1755855974737" MODIFIED="1755855989798">
<node TEXT="change annotation format to have image name" ID="ID_97676447" CREATED="1755856719192" MODIFIED="1755856728130"/>
<node TEXT="done" ID="ID_709584347" CREATED="1756475493668" MODIFIED="1756475494691"/>
</node>
<node TEXT="Run masked images through network saving the keypoints" ID="ID_258953007" CREATED="1755855952260" MODIFIED="1755855968811">
<node TEXT="save generated keypoints" ID="ID_1242605529" CREATED="1755863734028" MODIFIED="1755863740609"/>
<node TEXT="integrate keypoints into dataset format" ID="ID_1879699870" CREATED="1755863741336" MODIFIED="1755863750929"/>
</node>
</node>
<node TEXT="2. interpolate existing masks to neigbhors" ID="ID_394435942" CREATED="1755855598028" MODIFIED="1755855620103">
<node TEXT="identify keyframes with existing annotations" ID="ID_1317113615" CREATED="1755856527231" MODIFIED="1755856544515"/>
<node TEXT="get linear interpolation" ID="ID_520688605" CREATED="1755856749834" MODIFIED="1755856758431"/>
<node TEXT="generate vector fields" ID="ID_1369347518" CREATED="1756913904489" MODIFIED="1756913910288">
<node TEXT="calculate centroid of mask" ID="ID_811948204" CREATED="1756913912416" MODIFIED="1756913923142"/>
<node TEXT="one field for all entities" ID="ID_872336375" CREATED="1756914101267" MODIFIED="1756914109288"/>
</node>
<node TEXT="" ID="ID_399492374" CREATED="1756914096538" MODIFIED="1756914096538"/>
</node>
<node TEXT="3. apply pifpaf method" ID="ID_1330682327" CREATED="1755855620878" MODIFIED="1755855632891">
<node TEXT="regression error to vector fields" ID="ID_181343163" CREATED="1756913872514" MODIFIED="1756914124143"/>
<node TEXT="classification error to predict keypoints inside of field" ID="ID_613148303" CREATED="1756914124805" MODIFIED="1756914138494"/>
<node TEXT="fine tune model using classification for vector fields" ID="ID_54212834" CREATED="1756913881703" MODIFIED="1756913902006"/>
</node>
</node>
</node>
</node>
</node>
</map>
