var pc = null;

// data channel
var dc = null;

function negotiate() {
    pc.addTransceiver('video', {direction: 'recvonly'});
    pc.addTransceiver('audio', {direction: 'recvonly'});
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function(response) {
        return response.json();
    }).then(function(answer) {
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}

function start() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    if (document.getElementById('use-stun').checked) {
        config.iceServers = [{urls: ['stun:stun.l.google.com:19302']}];
    }

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', function(evt) {
        if (evt.track.kind == 'video') {
            document.getElementById('video').srcObject = evt.streams[0];
        } else {
            document.getElementById('audio').srcObject = evt.streams[0];
        }
    });

    if (document.getElementById('use-datachannel').checked) {
        var parameters = JSON.parse(document.getElementById('datachannel-parameters').value);

        dc = pc.createDataChannel('keyboard', parameters);
        // player1
        let keyMap1 = new Map([ 
            ['w', 'W'],
            ['a', 'A'],
            ['s', 'S'],
            ['d', 'D'],
            ['b', 'B'],
            ['v', 'V']
        ]);
        // player2
        let keyMap2 = new Map([ 
            ['ArrowLeft', 'Left'],
            ['ArrowRight', 'Right'],
            ['ArrowUp', 'Up'],
            ['ArrowDown', 'Down'],
            ['.', 'period'],
            [',', 'comma']
        ]);
        let keyMap = document.getElementById('player-id').value == '1' ? keyMap1 : keyMap2;
        document.onkeydown = function(e) {
            console.log(e.key);
            if (keyMap.has(e.key)) {
                dc.send('keydown' + keyMap.get(e.key));
            }
        };
        document.onkeyup = function(e) {
            if (keyMap.has(e.key)) {
                dc.send('keyup' + keyMap.get(e.key));
            }
        };
    }
    document.getElementById('player-id').style.display = 'none';
    document.getElementById('player-id-label').style.display = 'none';

    document.getElementById('start').style.display = 'none';
    negotiate();
    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    document.getElementById('stop').style.display = 'none';

    // close data channel
    if (dc) {
        dc.close();
    }

    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}
