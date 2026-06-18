
class MultiHeadAttention(nn.Module):
    """
    Computes multi-head attention. Supports nested or padded tensors.

    Args:
        E_q (int): Size of embedding dim for query
        E_k (int): Size of embedding dim for key
        E_v (int): Size of embedding dim for value
        E_total (int): Total embedding dim of combined heads post input projection. Each head
            has dim E_total // nheads
        nheads (int): Number of heads
        dropout (float, optional): Dropout probability. Default: 0.0
        bias (bool, optional): Whether to add bias to input projection. Default: True
    """

    def __init__(
        self,
        E_q: int,
        E_k: int,
        E_v: int,
        E_total: int,
        nheads: int,
        dropout: float = 0.0,
        bias=True,
        device=None,
        dtype=None,
    ):
        factory_kwargs = {"device": device, "dtype": dtype}
        super().__init__()
        self.nheads = nheads
        self.dropout = dropout
        self._qkv_same_embed_dim = E_q == E_k and E_q == E_v
        if self._qkv_same_embed_dim:
            self.packed_proj = nn.Linear(E_q, E_total * 3, bias=bias, **factory_kwargs)
        else:
            self.q_proj = nn.Linear(E_q, E_total, bias=bias, **factory_kwargs)
            self.k_proj = nn.Linear(E_k, E_total, bias=bias, **factory_kwargs)
            self.v_proj = nn.Linear(E_v, E_total, bias=bias, **factory_kwargs)
        E_out = E_q
        self.out_proj = nn.Linear(E_total, E_out, bias=bias, **factory_kwargs)
        assert E_total % nheads == 0, "Embedding dim is not divisible by nheads"
        self.E_head = E_total // nheads
        self.bias = bias

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask=None,
        is_causal=False,
    ) -> torch.Tensor:
        """
        Forward pass; runs the following process:
            1. Apply input projection
            2. Split heads and prepare for SDPA
            3. Run SDPA
            4. Apply output projection

        Args:
            query (torch.Tensor): query of shape (``N``, ``L_q``, ``E_qk``)
            key (torch.Tensor): key of shape (``N``, ``L_kv``, ``E_qk``)
            value (torch.Tensor): value of shape (``N``, ``L_kv``, ``E_v``)
            attn_mask (torch.Tensor, optional): attention mask of shape (``N``, ``L_q``, ``L_kv``) to pass to SDPA. Default: None
            is_causal (bool, optional): Whether to apply causal mask. Default: False

        Returns:
            attn_output (torch.Tensor): output of shape (N, L_t, E_q)
        """
        # Step 1. Apply input projection
        if self._qkv_same_embed_dim:
            if query is key and key is value:
                result = self.packed_proj(query)
                query, key, value = torch.chunk(result, 3, dim=-1)
            else:
                q_weight, k_weight, v_weight = torch.chunk(
                    self.packed_proj.weight, 3, dim=0
                )
                if self.bias:
                    q_bias, k_bias, v_bias = torch.chunk(
                        self.packed_proj.bias, 3, dim=0
                    )
                else:
                    q_bias, k_bias, v_bias = None, None, None
                query, key, value = (
                    F.linear(query, q_weight, q_bias),
                    F.linear(key, k_weight, k_bias),
                    F.linear(value, v_weight, v_bias),
                )

        else:
            query = self.q_proj(query)
            key = self.k_proj(key)
            value = self.v_proj(value)

        # Step 2. Split heads and prepare for SDPA
        # reshape query, key, value to separate by head
        # (N, L_t, E_total) -> (N, L_t, nheads, E_head) -> (N, nheads, L_t, E_head)
        query = query.unflatten(-1, [self.nheads, self.E_head]).transpose(1, 2)
        # (N, L_s, E_total) -> (N, L_s, nheads, E_head) -> (N, nheads, L_s, E_head)
        key = key.unflatten(-1, [self.nheads, self.E_head]).transpose(1, 2)
        # (N, L_s, E_total) -> (N, L_s, nheads, E_head) -> (N, nheads, L_s, E_head)
        value = value.unflatten(-1, [self.nheads, self.E_head]).transpose(1, 2)

        # Step 3. Run SDPA
        # (N, nheads, L_t, E_head)
        attn_output = F.scaled_dot_product_attention(
            query, key, value, dropout_p=self.dropout, is_causal=is_causal
        )
        # (N, nheads, L_t, E_head) -> (N, L_t, nheads, E_head) -> (N, L_t, E_total)
        attn_output = attn_output.transpose(1, 2).flatten(-2)

        # Step 4. Apply output projection
        # (N, L_t, E_total) -> (N, L_t, E_out)
        attn_output = self.out_proj(attn_output)

        return attn_output


class VectorHead(L.LightningModule):
    def _get_clf_model(self, config):
        model = torch.nn.Sequential(
            Superpoint.convPa, torch.nn.Relu(), Superpoint.convPb
        )
        model.load_statedict
        return model

    def _get_regress_model(self, config):
        return torch.nn.Sequential(
            nn.Linear(config.regressor.in_dim, config.regressor.in_dim),
            nn.ReLU(),
            nn.Linear(config.regressor.in_dim, config.regressor.out_dim),
        )

    # def _get_processor_model(self, config):
    #    mha_layer = MultiHeadAttention(**config.processor)
    #    return torch.compile(mha_layer)

    def __init__(backbone, config):
        super().__init__()
        self.backbone = backbone
        # self.processor = self._get_processor_model(config)
        self.regressor = self._get_regress_model(config)
        self.clf = self._get_clf_model(config)

    def forward(self, x):
        # inputs, target = batch
        with torch.no_grad():
            embeds = self.backbone(x)
        # new_embeds = self.processor(embeds, pts, embeds)
        pts = self.clf(embeds)
        mask < -pts
        vectors = self.regressor(new_embeds, mask)

        return pts, embeds, vectors, classif

    def training_step(self, batch, batch_idx):
        # training_step defines the train loop.
        x, target = batch
        x = x.view(x.size(0), -1)
        pts, embeds, vectors, classif = self(s)
        loss_vector = F.hinge_loss(vectors, target["vectors"])
        loss_clf = F.cross_entropy(
            classif,
        ) + F.l1_loss(
            vectors,
        )
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer


def gen_config(in_dim: int, nheads: int = 5):
    proc_conf_dict = {
        "E_q": 256,
        "E_v": 256,
        "E_k": 2,
        "E_total": 32,
        "nheads": 4,
        "dropout": False,
    }
    processor_config = SimpleNamespace(**proc_conf_dict)
    regressor_config = SimpleNamespace(in_dim=processor_config.E_q, out_dim=2)
    clf_config = SimpleNamespace(in_dim=processor_config.E_q, out_dim=1)
    return SimpleNamespace(
        processor=processor_config, regressor=regressor_config, classifier=clf_config
    )

def get_model_traindetector(num_classes=2, dropout=0.2):
    model = torchvision.models.mobilenet_v3_large(weights="IMAGENET1K_V2")
    weights = torchvision.models.get_weight("MobileNet_V3_Large_Weights.IMAGENET1K_V2")
    # stop
    # get number of input features for the classifier
    # in_features = model.classifier.in_features
    # replace the pre-trained head with a new one
    inverted_residual_setting, last_channel = _mobilenet_v3_conf("mobilenet_v3_large")
    # feat_dim = inverted_residual_setting[-1].out_channels
    feat_dim = 960
    model.classifier = torch.nn.Sequential(
        torch.nn.Linear(feat_dim, last_channel),
        torch.nn.Hardswish(inplace=True),
        torch.nn.Dropout(p=dropout, inplace=True),
        torch.nn.Linear(last_channel, num_classes),
    )  # train+other
    for m in model.classifier.modules():
        if isinstance(m, torch.nn.Conv2d):
            torch.nn.init.kaiming_normal_(m.weight, mode="fan_out")
            if m.bias is not None:
                torch.nn.init.zeros_(m.bias)
        elif isinstance(m, (torch.nn.BatchNorm2d, torch.nn.GroupNorm)):
            torch.nn.init.ones_(m.weight)
            torch.nn.init.zeros_(m.bias)
        elif isinstance(m, torch.nn.Linear):
            torch.nn.init.normal_(m.weight, 0, 0.01)
            torch.nn.init.zeros_(m.bias)
    # copy first layer of classif from pretrained
    state_dict = weights.get_state_dict()
    with torch.no_grad():
        model.classifier[0].weight.copy_(state_dict["classifier.0.weight"])
        model.classifier[0].bias.copy_(state_dict["classifier.0.bias"])
    # now get the number of input features for the mask classifier

    def nograds(layer_name):
        # no_grads = [f'features.{x}' for x in range(15)]
        no_grads = ["classifier.3"]
        return any(map(lambda x: layer_name.startswith(x), no_grads))

    for name, param in model.named_parameters():

        # if name.startswith('features') and not (name.startswith('features.15.block.2') or name.startswith('features.15.block.3') or name.startswith('features.16')):
        if not nograds(name):
            param.requires_grad = False
    return model


class MRRPointDetector(nn.Module):
    def __init__(self, run_config: Dict):
        super(MRRPointDetector, self).__init__()
        self.config = run_config
        weights_path = "./zoo/SuperPointPretrainedNetwork/superpoint_v1.pth"
        model = SuperPointNet()
        model.load_state_dict(
                torch.load(weights_path, map_location=lambda storage, loc: storage)
            )
        #model = model.float()
        self.detector = create_feature_extractor(model, {'convPb':'detector','conv4b':'hidden'})
        self.regressor = [#torch.nn.Sequential(
            torch.nn.Conv2d(128, 256, 3, stride=1, padding=1),
            torch.nn.Hardswish(inplace=True),
            torch.nn.Dropout(p=self.config['dropout'], inplace=True),
            #torch.nn.Linear(256, 2),
            torch.nn.Conv2d(256, 8*8*2, 1, stride=1, padding=0),
        ]#)

        self.shuffel = torch.nn.PixelShuffle(8)
        self.unshuffel = torch.nn.PixelUnshuffle(8)

    def forward(self, image):
        """
        Forward needs to return the point pairs at which an entity was detected.
        """
        #print('image', image.shape)
        out = self.detector(image)
        #semi = torch.nn.Softmax(out['detector'])[:-1]
        #dense = self.shuffel(semi)
        #xs,ys = torch.nonzero(dense >= self.config.conf_thresh)
        semi = F.softmax(out['detector'], dim=1)[:,0:64,:,:]
        dense = self.shuffel(semi).squeeze(1)
        B,H,W = dense.shape

        #pts = torch.nonzero(dense >= self.config['conf_thresh'], as_tuple=False)
        top_k = torch.topk(dense.flatten(), self.config['top_k'])
        idx = torch.unravel_index(top_k.indices, (H,W))
        X_pos, Y_pos = idx[1],idx[0]
        #print('dense',dense.shape)
        #confidents = dense[:,X_pos, Y_pos]

        fields = self.regressor[0](out['hidden'])
        #print(fields.shape)
        fields = self.regressor[1](fields)
        #fields = self.regressor[2](fields)
        fields = self.regressor[3](fields)#torch.transpose(fields,1,3))

        fields = self.shuffel(fields)
        fields = fields[:, :, Y_pos, X_pos].transpose(1,2)
        return idx, dense, fields
