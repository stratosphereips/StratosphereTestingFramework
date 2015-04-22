# How to work with labels in stf

The assignment of labels in stf is simple. However, it is not simple to decide which label corresponds to a connection. The problem cames from the definition of label to us. We want our labels to be very precise and descriptive. That is why the ```label``` command in stf is asking for some questions before putting a label. The questions are:

- Which is the direction of the connection, respect to the main host on it?
This question is directed to know if the data is comming _From_ or _To_ a _Normal_ or _Botnet_ host. The directionality is important to create different behavioral models later. For example, not all the data comming _to_ an infected computer should be labeled as _Botnet_.

- Which is the main decision on the data?
This question is basically to know if you consider the data as _Botnet_, _Normal_, etc.

- Which is the main protocol up to layer 4?
In this question we want to know which is in your opinion the main protocol that is characteristic of this connection. It can be HTTP, but it can also be P2P or ARP, depending on the connection.

- A description.
This description is useful to separate traffic from different websites for example, or different malware families.

We this information we _may_ be able to get a label name, however we have another issue to consider. It is common that two connections have the same origin, decision, main protocol and description, like for example **From-Botnet-UDP-DNS-DGA**. However, two DGA connections can have very different behavioral patterns. To distinguish them we add a number to the end of the label, in order to have **From-Botnet-UDP-DNS-DGA** and **From-Botnet-UDP-DNS-DGA**.
