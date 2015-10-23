alter table comment add parent_id int after post_id;
alter table comment add constraint comment_parent_id_fk foreign key(parent_id) references comment(id);

